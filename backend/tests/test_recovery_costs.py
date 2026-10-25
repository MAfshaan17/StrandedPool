from app.api.routes.recovery import _compare_user_entered_costs
from app.models.journey_booking import JourneyBooking


def test_cost_comparison_requires_matching_currency_and_marks_values_unverified():
    original = JourneyBooking(
        id=1,
        journey_id=1,
        kind="transport",
        provider="Sample rail",
        price_amount=1000,
        currency="INR",
    )

    comparable = _compare_user_entered_costs(
        [original],
        {"fare_amount": 1350, "currency": "INR"},
    )
    assert comparable == {
        "status": "user_entered_comparison",
        "currency": "INR",
        "original_amount": 1000,
        "proposed_amount": 1350,
        "difference": 350,
        "source_label": "Traveller-entered values; not independently verified",
    }

    incompatible = _compare_user_entered_costs(
        [original],
        {"fare_amount": 20, "currency": "USD"},
    )
    assert incompatible["status"] == "unavailable"
    assert "different currencies" in incompatible["reason"]
