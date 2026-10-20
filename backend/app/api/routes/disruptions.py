from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.disruption import Disruption
from ...models.journey import Journey
from ...schemas import DisruptionCreate, DisruptionRead

router = APIRouter()


@router.get("/disruptions", response_model=list[DisruptionRead], tags=["Disruptions"])
async def list_disruptions(db: AsyncSession = Depends(get_db)):
    result = await db.scalars(select(Disruption).order_by(Disruption.reported_at.desc()))
    return result.all()


@router.post(
    "/disruptions",
    response_model=DisruptionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Disruptions"],
)
async def report_disruption(payload: DisruptionCreate, db: AsyncSession = Depends(get_db)):
    if payload.journey_id is not None and await db.get(Journey, payload.journey_id) is None:
        raise HTTPException(status_code=404, detail="Journey not found")

    disruption = Disruption(**payload.model_dump())
    db.add(disruption)
    await db.commit()
    await db.refresh(disruption)
    return disruption
