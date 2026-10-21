from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_user
from ...db.session import get_db
from ...models.alternative import Alternative
from ...models.booking_dependency import BookingDependency
from ...models.disruption import Disruption
from ...models.journey import Journey
from ...models.journey_booking import JourneyBooking
from ...models.user import User
from ...schemas import AlternativeCreate, AlternativeScore
from ...services.recovery import are_pooling_compatible, score_alternative
from .journeys import get_journey_or_404

router = APIRouter()


@router.get("/transport/search", tags=["Recovery"])
async def search_transport(
    origin: str = Query(min_length=1, max_length=120),
    destination: str = Query(min_length=1, max_length=120),
):
    return {
        "status": "provider_unavailable",
        "origin": origin,
        "destination": destination,
        "provider": None,
        "source_label": "No authorized transport provider configured",
        "data_freshness": "No live data fetched",
        "checked_at": None,
        "options": [],
        "message": "No live transport results are available. Add options you have checked directly with a provider.",
    }


@router.post(
    "/journeys/{journey_id}/alternatives",
    response_model=AlternativeScore,
    status_code=status.HTTP_201_CREATED,
    tags=["Recovery"],
)
async def add_alternative(
    journey_id: int,
    payload: AlternativeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    journey = await get_journey_or_404(journey_id, db, user.id)
    alternative = Alternative(
        journey_id=journey_id,
        **payload.model_dump(),
    )
    db.add(alternative)
    await db.commit()
    await db.refresh(alternative)
    return score_alternative(alternative, journey)


@router.get(
    "/journeys/{journey_id}/alternatives",
    response_model=list[AlternativeScore],
    tags=["Recovery"],
)
async def list_alternatives(
    journey_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    journey = await get_journey_or_404(journey_id, db, user.id)
    alternatives = await db.scalars(
        select(Alternative)
        .where(Alternative.journey_id == journey_id)
        .order_by(Alternative.id)
    )
    scored = [score_alternative(item, journey) for item in alternatives.all()]
    feasible = [item for item in scored if item["feasible"]]
    return sorted(feasible, key=lambda item: (-item["score"], item["id"]))


@router.get("/journeys/{journey_id}/recovery", tags=["Recovery"])
async def get_recovery_plan(
    journey_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    journey = await get_journey_or_404(journey_id, db, user.id)
    disruptions = await db.scalars(
        select(Disruption)
        .where(Disruption.journey_id == journey_id)
        .order_by(Disruption.reported_at.desc(), Disruption.id.desc())
    )
    alternatives = await db.scalars(
        select(Alternative)
        .where(Alternative.journey_id == journey_id)
        .order_by(Alternative.id)
    )
    bookings = await db.scalars(
        select(JourneyBooking)
        .where(JourneyBooking.journey_id == journey_id)
        .order_by(JourneyBooking.created_at)
    )
    dependencies = await db.scalars(
        select(BookingDependency)
        .where(BookingDependency.journey_id == journey_id)
        .order_by(BookingDependency.id)
    )
    other_journeys = await db.scalars(
        select(Journey)
        .where(Journey.id != journey_id)
        .order_by(Journey.departure_at, Journey.id)
    )
    ranked = sorted(
        (
            scored
            for item in alternatives.all()
            if (scored := score_alternative(item, journey))["feasible"]
        ),
        key=lambda item: (-item["score"], item["id"]),
    )
    pooling_matches = [
        {
            "passenger_count": item.passenger_count,
        }
        for item in other_journeys.all()
        if are_pooling_compatible(journey, item)
    ]
    steps = [
        "Confirm the disruption and rebooking options directly with your transport operator.",
        "Add any alternative you have checked; prices and times will be ranked but not verified here.",
        "Contact affected accommodation or onward-booking providers about late arrival.",
    ]
    if pooling_matches:
        steps.append("Contact compatible travellers to discuss a shared ride; capacity and availability are unverified.")
    else:
        steps.append("No compatible traveller journeys are currently registered for a pooling proposal.")

    return {
        "journey": journey,
        "disruptions": disruptions.all(),
        "bookings": bookings.all(),
        "dependencies": dependencies.all(),
        "alternatives": ranked,
        "pooling": {
            "status": (
                "proposal_only" if journey.pooling_consent else "consent_required"
            ),
            "matches": pooling_matches,
            "total_consented_passengers": (
                journey.passenger_count
                + sum(match["passenger_count"] for match in pooling_matches)
                if journey.pooling_consent
                else 0
            ),
            "availability": "not verified",
        },
        "next_steps": steps,
    }


@router.get("/dashboard", tags=["Dashboard"])
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    journeys = await db.scalars(
        select(Journey)
        .where(Journey.owner_user_id == user.id)
        .order_by(Journey.departure_at, Journey.id)
    )
    disruptions = await db.scalars(
        select(Disruption)
        .where(Disruption.reporter_user_id == user.id)
        .order_by(Disruption.reported_at.desc(), Disruption.id.desc())
        .limit(5)
    )
    disruption_count = await db.scalar(
        select(func.count())
        .select_from(Disruption)
        .where(Disruption.reporter_user_id == user.id)
    )
    journey_list = journeys.all()
    disruption_list = disruptions.all()
    return {
        "journey_count": len(journey_list),
        "disruption_count": disruption_count or 0,
        "journeys": journey_list,
        "recent_disruptions": disruption_list,
        "data_notice": "Disruption reports and alternative details are traveller-provided and unverified.",
    }
