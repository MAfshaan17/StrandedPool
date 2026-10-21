from datetime import datetime, timezone
from typing import Any

from ..core.config import settings
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
    rejected_reasons = []
    if not destination_match:
        rejected_reasons.append("Destination does not match the journey.")
    if journey.budget_amount is not None:
        if alternative.fare_amount is None:
            rejected_reasons.append("Fare is unknown, so the budget constraint cannot be checked.")
        elif alternative.fare_amount > journey.budget_amount:
            rejected_reasons.append("Fare exceeds the journey budget.")
    if journey.arrive_by is not None:
        if alternative.arrival_at is None:
            rejected_reasons.append("Arrival time is unknown, so the deadline cannot be checked.")
        elif not arrives_on_time:
            rejected_reasons.append("Alternative arrives after the required deadline.")

    reasons = ["Destination matches" if destination_match else "Destination does not match"]
    cost_score = _cost_score(alternative.fare_amount, journey.budget_amount)
    time_score = _time_score(alternative.arrival_at, journey.departure_at, journey.arrive_by)
    reliability_score = (
        25.0 if "unverified" in alternative.source_label.casefold() else 100.0
    )
    if within_budget is True:
        reasons.append("Traveller-provided fare is within budget")
    elif within_budget is False:
        reasons.append("Traveller-provided fare exceeds budget")
    else:
        reasons.append("Fare or budget is unknown")

    if arrives_on_time is True:
        reasons.append("Traveller-provided arrival time meets the deadline")
    elif arrives_on_time is False:
        reasons.append("Traveller-provided arrival time is after the deadline")
    else:
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
        convenience_score = 100 * len(matched_constraints) / len(journey_constraints)
        reasons.append(
            f"Traveller marked {len(matched_constraints)} of "
            f"{len(journey_constraints)} stated constraints as met (unverified)"
        )
    else:
        convenience_score = 100.0
        reasons.append("No additional constraints were specified")

    score_breakdown = {
        "cost": cost_score,
        "time": time_score,
        "reliability": reliability_score,
        "convenience": convenience_score,
        "cost_weight": settings.cost_score_weight,
        "time_weight": settings.time_score_weight,
        "reliability_weight": settings.reliability_score_weight,
        "convenience_weight": settings.convenience_score_weight,
    }
    score = round(
        cost_score * settings.cost_score_weight
        + time_score * settings.time_score_weight
        + reliability_score * settings.reliability_score_weight
        + convenience_score * settings.convenience_score_weight
    )
    reasons.append(
        "Weighted score uses configured weights: "
        f"cost {settings.cost_score_weight:.0%}, "
        f"time {settings.time_score_weight:.0%}, "
        f"reliability {settings.reliability_score_weight:.0%}, "
        f"convenience {settings.convenience_score_weight:.0%}."
    )
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
        "feasible": not rejected_reasons,
        "rejected_reasons": rejected_reasons,
        "score_breakdown": score_breakdown,
        "reasons": reasons,
    }


def _cost_score(fare: float | None, budget: float | None) -> float:
    if fare is None or budget is None:
        return 50.0
    if budget == 0:
        return 100.0 if fare == 0 else 0.0
    return max(0.0, min(100.0, (budget - fare) / budget * 100))


def _time_score(
    arrival_at: datetime | None,
    departure_at: datetime,
    arrive_by: datetime | None,
) -> float:
    if arrival_at is None or arrive_by is None:
        return 50.0
    window_seconds = (
        _as_naive_utc(arrive_by) - _as_naive_utc(departure_at)
    ).total_seconds()
    if window_seconds <= 0:
        return 0.0
    remaining_seconds = (
        _as_naive_utc(arrive_by) - _as_naive_utc(arrival_at)
    ).total_seconds()
    return max(0.0, min(100.0, remaining_seconds / window_seconds * 100))


def are_pooling_compatible(first: Journey, second: Journey) -> bool:
    if not first.pooling_consent or not second.pooling_consent:
        return False
    if first.origin.strip().casefold() != second.origin.strip().casefold():
        return False
    if first.destination.strip().casefold() != second.destination.strip().casefold():
        return False
    first_departure = _as_naive_utc(first.departure_at)
    second_departure = _as_naive_utc(second.departure_at)
    return abs((first_departure - second_departure).total_seconds()) <= 2 * 60 * 60


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
