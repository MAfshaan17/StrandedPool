from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from ..models.journey_booking import JourneyBooking


def analyze_booking_cascade(
    bookings: list[JourneyBooking],
    dependency_edges: list[tuple[int, int]],
    affected_booking_id: int,
    disruption_status: str,
    delay_minutes: int | None = None,
) -> dict[str, Any]:
    booking_by_id = {booking.id: booking for booking in bookings}
    root = booking_by_id.get(affected_booking_id)
    if root is None:
        raise ValueError("Affected booking does not belong to this journey.")

    graph: dict[int, list[int]] = defaultdict(list)
    for predecessor_id, downstream_id in dependency_edges:
        if predecessor_id in booking_by_id and downstream_id in booking_by_id:
            graph[predecessor_id].append(downstream_id)

    impacts = [
        {
            "booking_id": root.id,
            "kind": root.kind,
            "impact": disruption_status,
            "severity": "high" if disruption_status == "cancelled" else "medium",
            "directly_affected": True,
            "expected_arrival": _expected_delayed_arrival(
                root,
                disruption_status,
                delay_minutes,
            ),
            "reason": (
                "The reported disruption directly affects this booking. "
                "Its status is not independently verified."
            ),
        }
    ]
    visited = {root.id}
    queue = deque([(root.id, _expected_delayed_arrival(root, disruption_status, delay_minutes))])
    cycles = _find_cycle_edges(graph)

    while queue:
        predecessor_id, predecessor_arrival = queue.popleft()
        for downstream_id in graph.get(predecessor_id, []):
            if downstream_id in visited:
                continue
            visited.add(downstream_id)
            downstream = booking_by_id[downstream_id]
            impact, reason, downstream_arrival = _evaluate_downstream(
                downstream,
                predecessor_arrival,
            )
            impacts.append(
                {
                    "booking_id": downstream.id,
                    "kind": downstream.kind,
                    "impact": impact,
                    "severity": (
                        "high" if impact == "missed_connection"
                        else "low" if impact == "not_affected"
                        else "medium"
                    ),
                    "directly_affected": False,
                    "expected_arrival": None,
                    "reason": reason,
                }
            )
            queue.append((downstream.id, downstream_arrival))

    return {
        "status": "analyzed",
        "source_label": "Traveller-provided disruption (unverified)",
        "affected_booking_id": root.id,
        "disruption_status": disruption_status,
        "delay_minutes": delay_minutes,
        "impacts": impacts,
        "cycles_detected": cycles,
        "automatically_cancelled_bookings": [],
        "limitations": [
            "Downstream impacts are estimates based on traveller-entered schedules and links.",
            "No bookings were changed or cancelled.",
        ],
    }


def _expected_delayed_arrival(
    booking: JourneyBooking,
    status: str,
    delay_minutes: int | None,
) -> datetime | None:
    if status != "delayed" or delay_minutes is None or booking.scheduled_end is None:
        return None
    return _utc(booking.scheduled_end) + timedelta(minutes=delay_minutes)


def _evaluate_downstream(
    booking: JourneyBooking,
    predecessor_arrival: datetime | None,
) -> tuple[str, str, datetime | None]:
    if predecessor_arrival is None or booking.scheduled_start is None:
        return (
            "at_risk",
            "A predecessor is disrupted, but available schedule data cannot establish feasibility.",
            None,
        )

    scheduled_start = _utc(booking.scheduled_start)
    if predecessor_arrival <= scheduled_start:
        return (
            "not_affected",
            "The estimated predecessor arrival is before this booking's scheduled start.",
            _utc(booking.scheduled_end) if booking.scheduled_end else None,
        )

    if booking.scheduled_end is None:
        return (
            "missed_connection",
            "The predecessor is estimated to arrive after this booking starts; this booking has no end time to propagate.",
            None,
        )
    delay = predecessor_arrival - scheduled_start
    return (
        "missed_connection",
        "The estimated predecessor arrival is later than this booking's scheduled start.",
        _utc(booking.scheduled_end) + delay,
    )


def _find_cycle_edges(graph: dict[int, list[int]]) -> list[dict[str, int]]:
    state: dict[int, int] = {}
    cycles: list[dict[str, int]] = []

    def visit(node: int) -> None:
        state[node] = 1
        for downstream in graph.get(node, []):
            if state.get(downstream) == 1:
                cycles.append({"from_booking_id": node, "to_booking_id": downstream})
            elif state.get(downstream, 0) == 0:
                visit(downstream)
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            visit(node)
    return cycles


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
