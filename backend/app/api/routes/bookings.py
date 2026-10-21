from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...core.auth import get_current_user
from ...models.journey_booking import JourneyBooking
from ...models.booking_dependency import BookingDependency
from ...models.user import User
from ...schemas import (
    BookingDependencyCreate,
    BookingDependencyRead,
    JourneyBookingCreate,
    JourneyBookingRead,
)
from .journeys import get_journey_or_404

router = APIRouter()


@router.get(
    "/journeys/{journey_id}/bookings",
    response_model=list[JourneyBookingRead],
    tags=["Bookings"],
)
async def list_bookings(
    journey_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_journey_or_404(journey_id, db, user.id)
    bookings = await db.scalars(
        select(JourneyBooking)
        .where(JourneyBooking.journey_id == journey_id)
        .order_by(JourneyBooking.created_at)
    )
    return bookings.all()


@router.post(
    "/journeys/{journey_id}/bookings",
    response_model=JourneyBookingRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Bookings"],
)
async def add_booking(
    journey_id: int,
    payload: JourneyBookingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_journey_or_404(journey_id, db, user.id)
    booking = JourneyBooking(journey_id=journey_id, **payload.model_dump())
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@router.post(
    "/journeys/{journey_id}/bookings/{booking_id}/dependencies",
    response_model=BookingDependencyRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Bookings"],
)
async def add_booking_dependency(
    journey_id: int,
    booking_id: int,
    payload: BookingDependencyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_journey_or_404(journey_id, db, user.id)
    predecessor = await db.get(JourneyBooking, booking_id)
    downstream = await db.get(JourneyBooking, payload.downstream_booking_id)
    if (
        predecessor is None
        or downstream is None
        or predecessor.journey_id != journey_id
        or downstream.journey_id != journey_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Both dependency bookings must belong to the specified journey.",
        )
    if booking_id == payload.downstream_booking_id:
        raise HTTPException(status_code=422, detail="A booking cannot depend on itself.")

    existing_edges = await db.execute(
        select(
            BookingDependency.predecessor_booking_id,
            BookingDependency.downstream_booking_id,
        ).where(BookingDependency.journey_id == journey_id)
    )
    edges = list(existing_edges.all())
    if _would_create_cycle(edges, booking_id, payload.downstream_booking_id):
        raise HTTPException(status_code=422, detail="This dependency would create a cycle.")
    if any(
        predecessor_id == booking_id and downstream_id == payload.downstream_booking_id
        for predecessor_id, downstream_id in edges
    ):
        raise HTTPException(status_code=409, detail="This dependency already exists.")

    dependency = BookingDependency(
        journey_id=journey_id,
        predecessor_booking_id=booking_id,
        downstream_booking_id=payload.downstream_booking_id,
        dependency_type=payload.dependency_type,
    )
    db.add(dependency)
    await db.commit()
    await db.refresh(dependency)
    return dependency


def _would_create_cycle(
    edges: list[tuple[int, int]],
    predecessor_id: int,
    downstream_id: int,
) -> bool:
    graph: dict[int, list[int]] = {}
    for source, target in edges:
        graph.setdefault(source, []).append(target)
    pending = [downstream_id]
    visited = set()
    while pending:
        current = pending.pop()
        if current == predecessor_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(graph.get(current, []))
    return False
