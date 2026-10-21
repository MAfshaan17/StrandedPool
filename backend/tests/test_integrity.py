from datetime import timezone

import pytest
from pydantic import ValidationError

from app.schemas import AlternativeCreate, JourneyBookingCreate, JourneyCreate


def test_journey_and_alternative_times_are_normalized_to_utc():
    journey = JourneyCreate(
        traveller_name="Demo",
        origin="Mangaluru",
        destination="Udupi",
        departure_at="2026-10-21T10:00:00+05:30",
        arrive_by="2026-10-21T14:00:00+05:30",
        budget_amount=1000,
        budget_currency="inr",
    )
    alternative = AlternativeCreate(
        mode="bus",
        provider="User checked",
        origin="Mangaluru",
        destination="Udupi",
        departure_at="2026-10-21T10:00:00+05:30",
        arrival_at="2026-10-21T11:30:00+05:30",
        currency="usd",
    )

    assert journey.departure_at.isoformat() == "2026-10-21T04:30:00+00:00"
    assert journey.departure_at.tzinfo == timezone.utc
    assert journey.budget_currency == "INR"
    assert alternative.departure_at.isoformat() == "2026-10-21T04:30:00+00:00"
    assert alternative.currency == "USD"


def test_naive_or_inconsistent_schedule_and_currency_inputs_are_rejected():
    with pytest.raises(ValidationError, match="UTC offset"):
        JourneyCreate(
            traveller_name="Demo",
            origin="Mangaluru",
            destination="Udupi",
            departure_at="2026-10-21T10:00:00",
        )

    with pytest.raises(ValidationError, match="arrive_by"):
        JourneyCreate(
            traveller_name="Demo",
            origin="Mangaluru",
            destination="Udupi",
            departure_at="2026-10-21T10:00:00Z",
            arrive_by="2026-10-21T09:00:00Z",
        )

    with pytest.raises(ValidationError, match="Currency"):
        AlternativeCreate(
            mode="bus",
            provider="User checked",
            origin="Mangaluru",
            destination="Udupi",
            currency="₹IN",
        )

    with pytest.raises(ValidationError, match="UTC offset"):
        JourneyBookingCreate(
            kind="transport",
            provider="Rail operator",
            scheduled_start="2026-10-21T10:00:00",
        )
