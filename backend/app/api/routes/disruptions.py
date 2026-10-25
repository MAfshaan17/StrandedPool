from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_user
from ...db.session import get_db
from ...models.disruption import Disruption
from ...models.journey import Journey
from ...models.journey_booking import JourneyBooking
from ...models.booking_dependency import BookingDependency
from ...models.user import User
from ...schemas import DisruptionAnalysisRequest, DisruptionCreate, DisruptionRead
from ...services.cascade import analyze_booking_cascade

router = APIRouter()


@router.get("/disruptions", response_model=list[DisruptionRead], tags=["Disruptions"])
async def list_disruptions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.scalars(
        select(Disruption)
        .where(Disruption.reporter_user_id == user.id)
        .order_by(Disruption.reported_at.desc(), Disruption.id.desc())
    )
    return result.all()


@router.post(
    "/disruptions",
    response_model=DisruptionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Disruptions"],
)
async def report_disruption(
    payload: DisruptionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.journey_id is not None:
        result = await db.scalar(
            select(Journey).where(
                Journey.id == payload.journey_id,
                Journey.owner_user_id == user.id,
            )
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Journey not found")

    disruption = Disruption(reporter_user_id=user.id, **payload.model_dump())
    db.add(disruption)
    await db.commit()
    await db.refresh(disruption)
    return disruption


@router.post("/v1/disruptions/analyze", tags=["Disruptions"])
async def analyze_disruption(
    payload: DisruptionAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _analyze_disruption(payload, db, user.id, simulated=False)


@router.post("/v1/disruptions/simulate", tags=["Disruptions"])
async def simulate_disruption(
    payload: DisruptionAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _analyze_disruption(payload, db, user.id, simulated=True)


async def _analyze_disruption(
    payload: DisruptionAnalysisRequest,
    db: AsyncSession,
    owner_user_id: int,
    simulated: bool,
):
    journey = await db.scalar(
        select(Journey).where(
            Journey.id == payload.journey_id,
            Journey.owner_user_id == owner_user_id,
        )
    )
    if journey is None:
        raise HTTPException(status_code=404, detail="Journey not found.")

    bookings = await db.scalars(
        select(JourneyBooking)
        .where(JourneyBooking.journey_id == journey.id)
        .order_by(JourneyBooking.id)
    )
    edges = await db.execute(
        select(
            BookingDependency.predecessor_booking_id,
            BookingDependency.downstream_booking_id,
        ).where(BookingDependency.journey_id == journey.id)
    )
    try:
        result = analyze_booking_cascade(
            bookings=list(bookings.all()),
            dependency_edges=list(edges.all()),
            affected_booking_id=payload.affected_booking_id,
            disruption_status=payload.disruption_status,
            delay_minutes=payload.delay_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if simulated:
        result["source_label"] = "SIMULATED disruption"
        result["status"] = "simulation"
    return result
