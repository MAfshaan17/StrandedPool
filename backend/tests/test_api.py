import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import get_db
from app.core.config import Settings
from app.main import app
from app.models import Base


def test_settings_load_environment_file(tmp_path):
    env_file = tmp_path / "settings.env"
    env_file.write_text(
        "APP_ENV=test\n"
        "FRONTEND_ORIGIN=http://localhost:3001\n"
        "DATABASE_URL=sqlite+aiosqlite:///./settings-test.db\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)
    assert settings.app_env == "test"
    assert settings.allowed_origins == ["http://localhost:3001"]
    assert settings.database_url == "sqlite+aiosqlite:///./settings-test.db"


def test_recovery_workflow_and_validation(tmp_path):
    async def exercise() -> None:
        database_path = tmp_path / "api-test.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async def override_database():
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_database
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                health = await client.get("/health")
                assert health.status_code == 200

                registration = await client.post(
                    "/api/auth/register",
                    json={
                        "email": "alex@example.test",
                        "password": "correct-horse-battery",
                    },
                )
                assert registration.status_code == 201
                client.headers["Authorization"] = (
                    f"Bearer {registration.json()['access_token']}"
                )

                created = await client.post(
                    "/api/journeys",
                    json={
                        "traveller_name": "Alex",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "departure_at": "2026-10-21T08:00:00Z",
                        "arrive_by": "2026-10-21T12:00:00Z",
                        "budget_amount": 1500,
                        "constraints": ["no overnight travel"],
                        "pooling_consent": True,
                    },
                )
                assert created.status_code == 201
                journey_id = created.json()["id"]

                companion = await client.post(
                    "/api/journeys",
                    json={
                        "traveller_name": "Sam",
                        "origin": "Mangaluru",
                        "destination": "udupi",
                        "departure_at": "2026-10-21T09:00:00Z",
                        "pooling_consent": True,
                    },
                )
                assert companion.status_code == 201

                booking = await client.post(
                    f"/api/journeys/{journey_id}/bookings",
                    json={
                        "kind": "accommodation",
                        "provider": "Coastal Inn",
                        "details": "Expected late arrival",
                    },
                )
                assert booking.status_code == 201

                disruption = await client.post(
                    "/api/disruptions",
                    json={
                        "journey_id": journey_id,
                        "title": "Delay reported",
                        "description": "Traveller reports a service delay.",
                        "transport_mode": "train",
                    },
                )
                assert disruption.status_code == 201
                assert disruption.json()["source_label"] == "Traveller report (unverified)"

                alternative = await client.post(
                    f"/api/journeys/{journey_id}/alternatives",
                    json={
                        "mode": "bus",
                        "provider": "User checked",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "arrival_at": "2026-10-21T11:00:00Z",
                        "fare_amount": 1200,
                        "constraints_satisfied": ["no overnight travel"],
                    },
                )
                assert alternative.status_code == 201
                assert alternative.json()["score"] == 30
                assert alternative.json()["score_breakdown"]["time"] == 25
                assert alternative.json()["source_label"] == "Traveller-provided (unverified)"
                assert alternative.json()["data_freshness"] == "Not verified"

                rejected_option = await client.post(
                    f"/api/journeys/{journey_id}/alternatives",
                    json={
                        "mode": "bus",
                        "provider": "Unverified entry",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "arrival_at": "2026-10-21T13:00:00Z",
                        "fare_amount": 1800,
                        "constraints_satisfied": ["wheelchair access"],
                    },
                )
                assert rejected_option.status_code == 201
                assert rejected_option.json()["score"] == 4
                assert rejected_option.json()["constraints_satisfied"] == []
                assert rejected_option.json()["feasible"] is False
                assert len(rejected_option.json()["rejected_reasons"]) == 2

                itinerary = await client.post(
                    "/api/v1/recovery/generate",
                    json={
                        "journey_id": journey_id,
                        "selected_alternative_id": alternative.json()["id"],
                    },
                )
                assert itinerary.status_code == 200
                assert itinerary.json()["proposed_alternative"]["status"] == "proposed_not_booked"
                assert itinerary.json()["booking_changes_made"] is False
                assert itinerary.json()["cost_comparison"]["status"] == "unavailable"
                saved_plan_id = itinerary.json()["plan_id"]
                saved_plans = await client.get(
                    f"/api/v1/journeys/{journey_id}/recovery-plans"
                )
                assert saved_plans.status_code == 200
                assert saved_plans.json()[0]["plan_id"] == saved_plan_id
                retrieved_plan = await client.get(
                    f"/api/v1/recovery/plans/{saved_plan_id}"
                )
                assert retrieved_plan.status_code == 200
                assert retrieved_plan.json()["plan_id"] == saved_plan_id
                assert retrieved_plan.json()["journey"]["id"] == journey_id

                simulated_itinerary = await client.post(
                    "/api/v1/recovery/generate",
                    json={
                        "journey_id": journey_id,
                        "affected_booking_id": booking.json()["id"],
                        "disruption_status": "cancelled",
                        "selected_alternative_id": alternative.json()["id"],
                    },
                )
                assert simulated_itinerary.status_code == 200
                assert simulated_itinerary.json()["disruption_analysis"]["impacts"][0]["impact"] == "cancelled"
                assert simulated_itinerary.json()["booking_changes_made"] is False

                rejected_itinerary = await client.post(
                    "/api/v1/recovery/generate",
                    json={
                        "journey_id": journey_id,
                        "selected_alternative_id": rejected_option.json()["id"],
                    },
                )
                assert rejected_itinerary.status_code == 422

                currency_mismatch = await client.post(
                    f"/api/journeys/{journey_id}/alternatives",
                    json={
                        "mode": "bus",
                        "provider": "Foreign-currency option",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "arrival_at": "2026-10-21T11:00:00Z",
                        "fare_amount": 20,
                        "currency": "USD",
                    },
                )
                assert currency_mismatch.status_code == 201
                assert currency_mismatch.json()["feasible"] is False
                assert currency_mismatch.json()["within_budget"] is None
                assert currency_mismatch.json()["currency_compatible"] is False
                assert any(
                    "currency does not match" in reason
                    for reason in currency_mismatch.json()["rejected_reasons"]
                )

                action_draft = await client.post(
                    "/api/v1/actions/draft",
                    json={
                        "action": "hotel_late_checkin",
                        "language": "en",
                        "provider_name": "Coastal Inn",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                    },
                )
                assert action_draft.status_code == 200
                assert action_draft.json()["requires_user_review"] is True
                assert action_draft.json()["sent"] is False

                recovery = await client.get(f"/api/journeys/{journey_id}/recovery")
                assert recovery.status_code == 200
                assert len(recovery.json()["bookings"]) == 1
                assert len(recovery.json()["disruptions"]) == 1
                assert recovery.json()["pooling"]["matches"][0]["passenger_count"] == 1
                assert recovery.json()["pooling"]["total_consented_passengers"] == 2
                assert set(recovery.json()["pooling"]["matches"][0]) == {"passenger_count"}

                unavailable = await client.get(
                    "/api/transport/search",
                    params={"origin": "Mangaluru", "destination": "Udupi"},
                )
                assert unavailable.status_code == 200
                assert unavailable.json()["status"] == "provider_unavailable"
                assert unavailable.json()["options"] == []
                provider_status = await client.get("/api/v1/providers/status")
                assert provider_status.status_code == 200
                assert (
                    provider_status.json()["providers"]["transport_inventory"]["status"]
                    == "unavailable"
                )
                assert (
                    provider_status.json()["providers"]["open_meteo"]["connection_verified"]
                    is False
                )

                invalid = await client.post(
                    "/api/journeys",
                    json={
                        "traveller_name": "",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "departure_at": "not-a-date",
                    },
                )
                assert invalid.status_code == 422

                dashboard = await client.get("/api/dashboard")
                assert dashboard.status_code == 200
                assert dashboard.json()["journey_count"] == 2
                assert dashboard.json()["disruption_count"] == 1
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(exercise())


def test_readiness_endpoint_uses_database(tmp_path):
    async def exercise() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ready-test.db'}")
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async def override_database():
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_database
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/health/ready")
                assert response.status_code == 200
                assert response.json() == {"status": "ready"}
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(exercise())


def test_authentication_and_journey_ownership(tmp_path):
    async def exercise() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'auth-test.db'}")
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async def override_database():
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_database
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                unauthenticated = await client.get("/api/journeys")
                assert unauthenticated.status_code == 401

                owner_registration = await client.post(
                    "/api/auth/register",
                    json={"email": "owner@example.test", "password": "owner-password-123"},
                )
                other_registration = await client.post(
                    "/api/auth/register",
                    json={"email": "other@example.test", "password": "other-password-123"},
                )
                assert owner_registration.status_code == 201
                assert other_registration.status_code == 201

                client.headers["Authorization"] = (
                    f"Bearer {owner_registration.json()['access_token']}"
                )
                created = await client.post(
                    "/api/journeys",
                    json={
                        "traveller_name": "Private traveller",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "departure_at": "2026-10-21T08:00:00Z",
                    },
                )
                assert created.status_code == 201
                journey_id = created.json()["id"]
                saved_plan = await client.post(
                    "/api/v1/recovery/generate",
                    json={"journey_id": journey_id},
                )
                assert saved_plan.status_code == 200

                client.headers["Authorization"] = (
                    f"Bearer {other_registration.json()['access_token']}"
                )
                private_journey = await client.get(f"/api/journeys/{journey_id}/recovery")
                private_plan = await client.get(
                    f"/api/v1/recovery/plans/{saved_plan.json()['plan_id']}"
                )
                private_plan_list = await client.get(
                    f"/api/v1/journeys/{journey_id}/recovery-plans"
                )
                listed = await client.get("/api/journeys")
                assert private_journey.status_code == 404
                assert private_plan.status_code == 404
                assert private_plan_list.status_code == 404
                assert listed.status_code == 200
                assert listed.json() == []
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(exercise())


def test_cors_allows_bearer_authorization_header():
    async def exercise() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.options(
                "/api/auth/login",
                headers={
                    "Origin": "http://127.0.0.1:3007",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,authorization",
                },
            )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3007"
        assert "authorization" in response.headers["access-control-allow-headers"].casefold()
        assert "content-type" in response.headers["access-control-allow-headers"].casefold()

    asyncio.run(exercise())


def test_development_cors_includes_local_preview_origins():
    settings = Settings(
        _env_file=None,
        app_env="development",
        frontend_origin="https://app.example.test",
    )

    assert "http://127.0.0.1:3007" in settings.allowed_origins
    assert "http://localhost:3007" in settings.allowed_origins
    assert "https://app.example.test" in settings.allowed_origins


def test_production_cors_uses_only_configured_origins():
    settings = Settings(
        _env_file=None,
        app_env="production",
        frontend_origin="https://app.example.test",
        auth_secret_key="s" * 32,
    )

    assert settings.allowed_origins == ["https://app.example.test"]
