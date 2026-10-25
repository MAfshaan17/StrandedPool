import asyncio
from datetime import datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import get_db
from app.main import app
from app.models import Base
from app.models.journey_booking import JourneyBooking
from app.services.cascade import analyze_booking_cascade


def test_cascade_propagates_known_delay_and_handles_cycles():
    start = datetime(2026, 10, 21, 8, tzinfo=timezone.utc)
    train = JourneyBooking(
        id=1,
        kind="transport",
        provider="Train",
        scheduled_start=start,
        scheduled_end=start + timedelta(hours=2),
    )
    cab = JourneyBooking(
        id=2,
        kind="transport",
        provider="Cab",
        scheduled_start=start + timedelta(hours=2, minutes=30),
        scheduled_end=start + timedelta(hours=3),
    )
    hotel = JourneyBooking(
        id=3,
        kind="accommodation",
        provider="Hotel",
        scheduled_start=start + timedelta(hours=6),
        scheduled_end=start + timedelta(hours=7),
    )

    result = analyze_booking_cascade(
        [train, cab, hotel],
        [(1, 2), (2, 3), (3, 2)],
        affected_booking_id=1,
        disruption_status="delayed",
        delay_minutes=60,
    )

    assert [impact["impact"] for impact in result["impacts"]] == [
        "delayed",
        "missed_connection",
        "not_affected",
    ]
    assert result["impacts"][0]["expected_arrival"] == datetime(
        2026, 10, 21, 11, tzinfo=timezone.utc
    )
    assert result["cycles_detected"] == [{"from_booking_id": 3, "to_booking_id": 2}]
    assert result["automatically_cancelled_bookings"] == []


def test_simulated_cancellation_endpoint_and_dependency_cycle_validation(tmp_path):
    async def exercise() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'cascade.db'}")
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
                registration = await client.post(
                    "/api/auth/register",
                    json={
                        "email": "cascade@example.test",
                        "password": "cascade-password-123",
                    },
                )
                assert registration.status_code == 201
                client.headers["Authorization"] = (
                    f"Bearer {registration.json()['access_token']}"
                )
                journey = await client.post(
                    "/api/journeys",
                    json={
                        "traveller_name": "Demo",
                        "origin": "Mangaluru",
                        "destination": "Udupi",
                        "departure_at": "2026-10-21T08:00:00Z",
                    },
                )
                journey_id = journey.json()["id"]
                bookings = []
                for kind, provider, start, end in [
                    (
                        "transport",
                        "Train",
                        "2026-10-21T08:00:00Z",
                        "2026-10-21T10:00:00Z",
                    ),
                    (
                        "transport",
                        "Cab",
                        "2026-10-21T10:30:00Z",
                        "2026-10-21T11:00:00Z",
                    ),
                    (
                        "accommodation",
                        "Hotel",
                        "2026-10-21T14:00:00Z",
                        "2026-10-21T15:00:00Z",
                    ),
                ]:
                    response = await client.post(
                        f"/api/journeys/{journey_id}/bookings",
                        json={
                            "kind": kind,
                            "provider": provider,
                            "scheduled_start": start,
                            "scheduled_end": end,
                        },
                    )
                    assert response.status_code == 201
                    bookings.append(response.json())

                first_edge = await client.post(
                    f"/api/journeys/{journey_id}/bookings/{bookings[0]['id']}/dependencies",
                    json={"downstream_booking_id": bookings[1]["id"], "dependency_type": "pickup"},
                )
                assert first_edge.status_code == 201
                second_edge = await client.post(
                    f"/api/journeys/{journey_id}/bookings/{bookings[1]['id']}/dependencies",
                    json={"downstream_booking_id": bookings[2]["id"], "dependency_type": "check_in"},
                )
                assert second_edge.status_code == 201

                cycle = await client.post(
                    f"/api/journeys/{journey_id}/bookings/{bookings[2]['id']}/dependencies",
                    json={"downstream_booking_id": bookings[0]["id"]},
                )
                assert cycle.status_code == 422
                assert "cycle" in cycle.json()["detail"]

                result = await client.post(
                    "/api/v1/disruptions/simulate",
                    json={
                        "journey_id": journey_id,
                        "affected_booking_id": bookings[0]["id"],
                        "disruption_status": "cancelled",
                    },
                )
                assert result.status_code == 200
                body = result.json()
                assert body["status"] == "simulation"
                assert body["source_label"] == "SIMULATED disruption"
                assert [impact["impact"] for impact in body["impacts"]] == [
                    "cancelled",
                    "at_risk",
                    "at_risk",
                ]
                assert body["automatically_cancelled_bookings"] == []

                invalid_delay = await client.post(
                    "/api/v1/disruptions/analyze",
                    json={
                        "journey_id": journey_id,
                        "affected_booking_id": bookings[0]["id"],
                        "disruption_status": "delayed",
                    },
                )
                assert invalid_delay.status_code == 422
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(exercise())
