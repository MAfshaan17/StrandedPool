from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.journey_booking import JourneyBooking
from ...schemas import JourneyBookingCreate, JourneyBookingRead
from .journeys import get_journey_or_404

router = APIRouter()


@router.get(
    "/journeys/{journey_id}/bookings",
    response_model=list[JourneyBookingRead],
    tags=["Bookings"],
)
async def list_bookings(journey_id: int, db: AsyncSession = Depends(get_db)):
    await get_journey_or_404(journey_id, db)
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
):
    await get_journey_or_404(journey_id, db)
    booking = JourneyBooking(journey_id=journey_id, **payload.model_dump())
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking
