from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

from ..models.journey_booking import JourneyBooking
from ..schemas import ActionDraftRequest
from .actions import draft_action
from .cascade import analyze_booking_cascade


@dataclass(frozen=True)
class DemoTraveller:
    traveller_id: str
    passenger_count: int
    origin: str
    destination: str
    departure_at: datetime
    arrive_by: datetime
    budget_amount: float
    currency: str
    existing_fare_amount: float
    pooling_consent: bool


@dataclass(frozen=True)
class DemoTransportOption:
    option_id: str
    label: str
    capacity: int
    total_fare: float
    currency: str
    departure_at: datetime
    arrival_at: datetime
    origin: str
    destination: str
    shared_vehicle: bool


def run_demo_simulation() -> dict[str, Any]:
    """Run a deterministic, explicitly simulated capacity-aware recovery scenario."""
    start = datetime(2026, 10, 21, 8, tzinfo=timezone.utc)
    travellers = [
        DemoTraveller(
            traveller_id=f"sample-{index}",
            passenger_count=1,
            origin="Mangaluru",
            destination="Udupi",
            departure_at=start + timedelta(hours=1),
            arrive_by=start + timedelta(hours=6),
            budget_amount=2000,
            currency="INR",
            existing_fare_amount=1000,
            pooling_consent=True,
        )
        for index in range(1, 4)
    ]
    options = [
        DemoTransportOption(
            option_id=f"private-taxi-{index}",
            label="SIMULATED private taxi",
            capacity=1,
            total_fare=1500,
            currency="INR",
            departure_at=start + timedelta(hours=1),
            arrival_at=start + timedelta(hours=4, minutes=30),
            origin="Mangaluru",
            destination="Udupi",
            shared_vehicle=False,
        )
        for index in range(1, 4)
    ]
    options.append(
        DemoTransportOption(
            option_id="pooled-taxi",
            label="SIMULATED shared taxi",
            capacity=3,
            total_fare=3300,
            currency="INR",
            departure_at=start + timedelta(hours=1),
            arrival_at=start + timedelta(hours=4, minutes=45),
            origin="Mangaluru",
            destination="Udupi",
            shared_vehicle=True,
        )
    )

    generation_started = perf_counter()
    non_pool_assignments = _allocate_independently(travellers, options)
    pool_assignments = _allocate_with_pooling(travellers, options)
    cascade = _demo_cascade(start)

    itinerary = {
        "source_label": "SIMULATED demo data; no live provider inventory",
        "original_timeline": [
            {"mode": "train", "departure_at": start, "arrival_at": start + timedelta(hours=2)},
            {"mode": "cab pickup", "departure_at": start + timedelta(hours=2, minutes=30)},
            {"mode": "hotel check-in", "departure_at": start + timedelta(hours=5)},
        ],
        "proposed_timeline": [
            {
                "mode": pool_assignments[0]["option_label"] if pool_assignments else None,
                "departure_at": options[-1].departure_at if pool_assignments else None,
                "arrival_at": options[-1].arrival_at if pool_assignments else None,
                "status": "proposed_not_booked",
            }
        ],
        "booking_changes_made": False,
        "next_steps": [
            "Confirm service recovery directly with the train operator.",
            "Verify the simulated taxi option with a real provider before making decisions.",
            "Contact the hotel about the estimated arrival time.",
        ],
    }
    generation_ms = (perf_counter() - generation_started) * 1000

    hotel_message = draft_action(
        ActionDraftRequest(
            action="hotel_late_checkin",
            language="en",
            provider_name="Sample Hotel",
            origin="Mangaluru",
            destination="Udupi",
        )
    )
    refund_message = draft_action(
        ActionDraftRequest(
            action="refund_inquiry",
            language="en",
            provider_name="Sample Rail Operator",
            origin="Mangaluru",
            destination="Udupi",
        )
    )

    return {
        "data_label": "SIMULATED demo only",
        "travellers": [
            {
                "traveller_id": traveller.traveller_id,
                "passenger_count": traveller.passenger_count,
                "pooling_consent": traveller.pooling_consent,
            }
            for traveller in travellers
        ],
        "linked_bookings": [
            {"booking_id": 1, "kind": "train", "provider": "Sample Rail Operator"},
            {"booking_id": 2, "kind": "cab pickup", "provider": "Sample Cab"},
            {"booking_id": 3, "kind": "accommodation", "provider": "Sample Hotel"},
        ],
        "disruption_analysis": cascade,
        "feasible_options": [
            {
                "option_id": option.option_id,
                "label": option.label,
                "capacity": option.capacity,
                "total_fare": option.total_fare,
                "currency": option.currency,
            }
            for option in options
        ],
        "allocation_comparison": {
            "same_travellers_and_constraints": True,
            "non_pooling": _allocation_metrics(non_pool_assignments, travellers),
            "pooling": _allocation_metrics(pool_assignments, travellers),
        },
        "pooling_utilization": (
            {
                "passengers_assigned": sum(
                    assignment["passenger_count"] for assignment in pool_assignments
                ),
                "capacity": options[-1].capacity,
                "utilization_percent": round(
                    sum(
                        assignment["passenger_count"]
                        for assignment in pool_assignments
                    )
                    / options[-1].capacity
                    * 100,
                    1,
                ),
            }
            if pool_assignments
            else {"passengers_assigned": 0, "capacity": options[-1].capacity, "utilization_percent": 0}
        ),
        "recovery_itinerary": itinerary,
        "metrics": {
            "travellers_assigned_feasible_alternatives": _allocation_metrics(
                pool_assignments,
                travellers,
            )["assigned_travellers"],
            "total_additional_cost_pooling": _additional_cost(
                pool_assignments,
                travellers,
            ),
            "average_additional_cost_per_traveller_pooling": _average_additional_cost(
                pool_assignments,
                travellers,
            ),
            "total_additional_cost_non_pooling": _additional_cost(
                non_pool_assignments,
                travellers,
            ),
            "average_additional_cost_per_traveller_non_pooling": _average_additional_cost(
                non_pool_assignments,
                travellers,
            ),
            "recovery_plan_generation_ms": round(generation_ms, 3),
            "downstream_bookings_identified": max(len(cascade["impacts"]) - 1, 0),
        },
        "editable_action_drafts": {
            "hotel_late_checkin": hotel_message,
            "refund_inquiry": refund_message,
        },
    }


def _allocate_independently(
    travellers: list[DemoTraveller],
    options: list[DemoTransportOption],
) -> list[dict[str, Any]]:
    assignments = []
    used_option_ids: set[str] = set()
    for traveller in travellers:
        feasible = [
            option
            for option in options
            if not option.shared_vehicle
            and option.option_id not in used_option_ids
            and _option_is_feasible(option, [traveller])
        ]
        if not feasible:
            continue
        selected = min(feasible, key=lambda option: (option.total_fare, option.option_id))
        used_option_ids.add(selected.option_id)
        assignments.append(_assignment(selected, [traveller]))
    return assignments


def _allocate_with_pooling(
    travellers: list[DemoTraveller],
    options: list[DemoTransportOption],
) -> list[dict[str, Any]]:
    if not travellers or not all(traveller.pooling_consent for traveller in travellers):
        return _allocate_independently(travellers, options)
    if not _travellers_are_compatible(travellers):
        return _allocate_independently(travellers, options)
    group_options = [
        option
        for option in options
        if option.shared_vehicle and _option_is_feasible(option, travellers)
    ]
    if not group_options:
        return _allocate_independently(travellers, options)
    selected = min(group_options, key=lambda option: (option.total_fare, option.option_id))
    return [_assignment(selected, travellers)]


def _travellers_are_compatible(travellers: list[DemoTraveller]) -> bool:
    first = travellers[0]
    for traveller in travellers[1:]:
        if (
            traveller.origin.strip().casefold() != first.origin.strip().casefold()
            or traveller.destination.strip().casefold()
            != first.destination.strip().casefold()
            or traveller.currency != first.currency
            or abs(
                (traveller.departure_at - first.departure_at).total_seconds()
            )
            > 2 * 60 * 60
        ):
            return False
    return True


def _option_is_feasible(
    option: DemoTransportOption,
    travellers: list[DemoTraveller],
) -> bool:
    passenger_total = sum(traveller.passenger_count for traveller in travellers)
    if option.capacity < passenger_total:
        return False
    if any(
        not traveller.pooling_consent
        for traveller in travellers
    ) and option.shared_vehicle:
        return False
    if any(
        option.currency != traveller.currency
        or option.origin.strip().casefold() != traveller.origin.strip().casefold()
        or option.destination.strip().casefold()
        != traveller.destination.strip().casefold()
        or option.departure_at < traveller.departure_at - timedelta(hours=2)
        or option.departure_at > traveller.departure_at + timedelta(hours=2)
        or option.arrival_at > traveller.arrive_by
        for traveller in travellers
    ):
        return False
    fare_per_passenger = option.total_fare / passenger_total
    return all(fare_per_passenger <= traveller.budget_amount for traveller in travellers)


def _assignment(
    option: DemoTransportOption,
    travellers: list[DemoTraveller],
) -> dict[str, Any]:
    passenger_total = sum(traveller.passenger_count for traveller in travellers)
    return {
        "option_id": option.option_id,
        "option_label": option.label,
        "traveller_ids": [traveller.traveller_id for traveller in travellers],
        "passenger_count": passenger_total,
        "capacity": option.capacity,
        "total_fare": option.total_fare,
        "currency": option.currency,
        "fare_per_passenger": option.total_fare / passenger_total,
        "status": "SIMULATED_NOT_BOOKED",
    }


def _allocation_metrics(
    assignments: list[dict[str, Any]],
    travellers: list[DemoTraveller],
) -> dict[str, Any]:
    assigned_ids = {
        traveller_id
        for assignment in assignments
        for traveller_id in assignment["traveller_ids"]
    }
    cost = sum(assignment["total_fare"] for assignment in assignments)
    baseline = sum(
        traveller.existing_fare_amount
        * traveller.passenger_count
        for traveller in travellers
    )
    total_passengers = len(assigned_ids)
    return {
        "assigned_travellers": total_passengers,
        "unassigned_travellers": len(travellers) - total_passengers,
        "total_transport_cost": cost,
        "total_additional_cost": cost - baseline,
        "average_additional_cost_per_assigned_traveller": (
            round((cost - baseline) / total_passengers, 2)
            if total_passengers
            else None
        ),
        "assignments": assignments,
    }


def _additional_cost(
    assignments: list[dict[str, Any]],
    travellers: list[DemoTraveller],
) -> float:
    assigned = {
        traveller_id
        for assignment in assignments
        for traveller_id in assignment["traveller_ids"]
    }
    baseline = sum(
        traveller.existing_fare_amount * traveller.passenger_count
        for traveller in travellers
        if traveller.traveller_id in assigned
    )
    return sum(item["total_fare"] for item in assignments) - baseline


def _average_additional_cost(
    assignments: list[dict[str, Any]],
    travellers: list[DemoTraveller],
) -> float | None:
    metrics = _allocation_metrics(assignments, travellers)
    return metrics["average_additional_cost_per_assigned_traveller"]


def _demo_cascade(start: datetime) -> dict[str, Any]:
    bookings = [
        JourneyBooking(
            id=1,
            kind="transport",
            provider="Sample Rail Operator",
            scheduled_start=start,
            scheduled_end=start + timedelta(hours=2),
        ),
        JourneyBooking(
            id=2,
            kind="transport",
            provider="Sample Cab",
            scheduled_start=start + timedelta(hours=2, minutes=30),
            scheduled_end=start + timedelta(hours=3),
        ),
        JourneyBooking(
            id=3,
            kind="accommodation",
            provider="Sample Hotel",
            scheduled_start=start + timedelta(hours=5),
            scheduled_end=start + timedelta(hours=6),
        ),
    ]
    return analyze_booking_cascade(
        bookings=bookings,
        dependency_edges=[(1, 2), (2, 3)],
        affected_booking_id=1,
        disruption_status="cancelled",
    )
