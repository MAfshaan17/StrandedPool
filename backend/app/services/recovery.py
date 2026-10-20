from datetime import datetime, timezone
from typing import Any

from ..models.alternative import Alternative
from ..models.journey import Journey


def score_alternative(alternative: Alternative, journey: Journey) -> dict[str, Any]:
    destination_match = alternative.destination.strip().casefold() == journey.destination.strip().casefold()
    within_budget = (
        alternative.fare_amount <= journey.budget_amount
        if alternative.fare_amount is not None and journey.budget_amount is not None
        else None
    )
    arrives_on_time = (
        alternative.arrival_at <= journey.arrive_by
        if alternative.arrival_at is not None and journey.arrive_by is not None
        else None
    )

    score = 30 if destination_match else 0
    reasons = ["Destination matches" if destination_match else "Destination does not match"]
    if within_budget is True:
        score += 25
        reasons.append("Traveller-provided fare is within budget")
    elif within_budget is False:
        reasons.append("Traveller-provided fare exceeds budget")
    else:
        score += 12
        reasons.append("Fare or budget is unknown")

    if arrives_on_time is True:
        score += 25
        reasons.append("Traveller-provided arrival time meets the deadline")
    elif arrives_on_time is False:
        reasons.append("Traveller-provided arrival time is after the deadline")
    else:
        score += 12
        reasons.append("Arrival time or deadline is unknown")

    journey_constraints = {
        constraint.strip().casefold()
        for constraint in journey.constraints
        if constraint.strip()
    }
    asserted_constraints = {
        constraint.strip().casefold()
        for constraint in alternative.constraints_satisfied
        if constraint.strip()
    }
    matched_constraints = journey_constraints & asserted_constraints
    if journey_constraints:
        score += round(20 * len(matched_constraints) / len(journey_constraints))
        reasons.append(
            f"Traveller marked {len(matched_constraints)} of "
            f"{len(journey_constraints)} stated constraints as met (unverified)"
        )
    else:
        score += 20
        reasons.append("No additional constraints were specified")

    return {
        "id": alternative.id,
        "journey_id": alternative.journey_id,
        "mode": alternative.mode,
        "provider": alternative.provider,
        "origin": alternative.origin,
        "destination": alternative.destination,
        "departure_at": alternative.departure_at,
        "arrival_at": alternative.arrival_at,
        "fare_amount": alternative.fare_amount,
        "constraints_satisfied": sorted(matched_constraints),
        "source_label": alternative.source_label,
        "entered_at": alternative.entered_at,
        "data_freshness": "Not verified",
        "score": score,
        "destination_match": destination_match,
        "within_budget": within_budget,
        "arrives_on_time": arrives_on_time,
        "reasons": reasons,
    }


def are_pooling_compatible(first: Journey, second: Journey) -> bool:
    if first.destination.strip().casefold() != second.destination.strip().casefold():
        return False
    first_departure = _as_naive_utc(first.departure_at)
    second_departure = _as_naive_utc(second.departure_at)
    return abs((first_departure - second_departure).total_seconds()) <= 2 * 60 * 60


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
