from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.journey import Journey
from ...models.user import User
from ...core.auth import get_current_user
from ...schemas import JourneyCreate, JourneyRead

router = APIRouter()


@router.get("/journeys", response_model=list[JourneyRead], tags=["Journeys"])
async def list_journeys(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.scalars(
        select(Journey)
        .where(Journey.owner_user_id == user.id)
        .order_by(Journey.departure_at, Journey.id)
    )
    return result.all()


@router.post(
    "/journeys",
    response_model=JourneyRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Journeys"],
)
async def create_journey(
    payload: JourneyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    journey = Journey(owner_user_id=user.id, **payload.model_dump())
    db.add(journey)
    await db.commit()
    await db.refresh(journey)
    return journey


async def get_journey_or_404(
    journey_id: int,
    db: AsyncSession,
    owner_user_id: int,
) -> Journey:
    journey = await db.scalar(
        select(Journey).where(
            Journey.id == journey_id,
            Journey.owner_user_id == owner_user_id,
        )
    )
    if journey is None:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey
