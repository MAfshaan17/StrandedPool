from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JourneyCreate(BaseModel):
    traveller_name: str = Field(min_length=1, max_length=80)
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    departure_at: datetime
    arrive_by: datetime | None = None
    budget_amount: float | None = Field(default=None, ge=0)
    constraints: list[str] = Field(default_factory=list, max_length=12)


class JourneyRead(JourneyCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DisruptionCreate(BaseModel):
    journey_id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=3, max_length=2000)
    transport_mode: str | None = Field(default=None, max_length=40)


class DisruptionRead(BaseModel):
    id: int
    journey_id: int | None
    title: str
    description: str
    transport_mode: str | None
    status: str
    source_label: str
    reported_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlternativeCreate(BaseModel):
    mode: Literal["bus", "train", "flight", "taxi", "other"]
    provider: str = Field(min_length=1, max_length=120)
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    departure_at: datetime | None = None
    arrival_at: datetime | None = None
    fare_amount: float | None = Field(default=None, ge=0)
    constraints_satisfied: list[str] = Field(default_factory=list, max_length=12)


class AlternativeScore(BaseModel):
    id: int
    journey_id: int
    mode: str
    provider: str
    origin: str
    destination: str
    departure_at: datetime | None
    arrival_at: datetime | None
    fare_amount: float | None
    constraints_satisfied: list[str]
    source_label: str
    entered_at: datetime
    data_freshness: str
    score: int
    destination_match: bool
    within_budget: bool | None
    arrives_on_time: bool | None
    reasons: list[str]

    model_config = ConfigDict(from_attributes=True)


class JourneyBookingCreate(BaseModel):
    kind: Literal["transport", "accommodation", "connection", "appointment", "other"]
    provider: str = Field(min_length=1, max_length=120)
    reference: str | None = Field(default=None, max_length=80)
    details: str | None = Field(default=None, max_length=2000)


class JourneyBookingRead(BaseModel):
    id: int
    journey_id: int
    kind: str
    provider: str
    reference: str | None
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
