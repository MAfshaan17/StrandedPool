from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.journey import Journey
from ...schemas import JourneyCreate, JourneyRead

router = APIRouter()


@router.get("/journeys", response_model=list[JourneyRead], tags=["Journeys"])
async def list_journeys(db: AsyncSession = Depends(get_db)):
    result = await db.scalars(
        select(Journey).order_by(Journey.departure_at, Journey.id)
    )
    return result.all()


@router.post(
    "/journeys",
    response_model=JourneyRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Journeys"],
)
async def create_journey(payload: JourneyCreate, db: AsyncSession = Depends(get_db)):
    journey = Journey(**payload.model_dump())
    db.add(journey)
    await db.commit()
    await db.refresh(journey)
    return journey


async def get_journey_or_404(journey_id: int, db: AsyncSession) -> Journey:
    journey = await db.get(Journey, journey_id)
    if journey is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey
