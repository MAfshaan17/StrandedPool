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
                assert alternative.json()["score"] == 100
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
                assert rejected_option.json()["score"] == 30
                assert rejected_option.json()["constraints_satisfied"] == []

                recovery = await client.get(f"/api/journeys/{journey_id}/recovery")
                assert recovery.status_code == 200
                assert len(recovery.json()["bookings"]) == 1
                assert len(recovery.json()["disruptions"]) == 1
                assert recovery.json()["pooling"]["matches"][0]["traveller_name"] == "Sam"

                unavailable = await client.get(
                    "/api/transport/search",
                    params={"origin": "Mangaluru", "destination": "Udupi"},
                )
                assert unavailable.status_code == 200
                assert unavailable.json()["status"] == "provider_unavailable"
                assert unavailable.json()["options"] == []

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
