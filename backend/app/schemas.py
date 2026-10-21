from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JourneyCreate(BaseModel):
    traveller_name: str = Field(min_length=1, max_length=80)
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    departure_at: datetime
    arrive_by: datetime | None = None
    budget_amount: float | None = Field(default=None, ge=0)
    constraints: list[str] = Field(default_factory=list, max_length=12)
    pooling_consent: bool = False
    passenger_count: int = Field(default=1, ge=1, le=12)


class JourneyRead(JourneyCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthRegister(BaseModel):
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @model_validator(mode="after")
    def normalize_and_validate_email(self):
        self.email = self.email.strip().casefold()
        if "@" not in self.email or self.email.startswith("@") or "." not in self.email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        if any(character.isspace() for character in self.email):
            raise ValueError("Enter a valid email address.")
        return self


class AuthLogin(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AuthUser(BaseModel):
    id: int
    email: str
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AuthToken(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: AuthUser


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
    feasible: bool
    rejected_reasons: list[str]
    score_breakdown: dict[str, float]
    reasons: list[str]

    model_config = ConfigDict(from_attributes=True)


class JourneyBookingCreate(BaseModel):
    kind: Literal["transport", "accommodation", "connection", "appointment", "other"]
    provider: str = Field(min_length=1, max_length=120)
    reference: str | None = Field(default=None, max_length=80)
    details: str | None = Field(default=None, max_length=2000)
    origin: str | None = Field(default=None, max_length=120)
    destination: str | None = Field(default=None, max_length=120)
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
    latest_acceptable_arrival: datetime | None = None
    price_amount: float | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: Literal["scheduled"] = "scheduled"

    @model_validator(mode="after")
    def validate_booking_times(self):
        for timestamp_name in (
            "scheduled_start",
            "scheduled_end",
            "latest_acceptable_arrival",
        ):
            timestamp = getattr(self, timestamp_name)
            if timestamp is not None and timestamp.utcoffset() is None:
                raise ValueError(f"{timestamp_name} must include a UTC offset")
        if self.scheduled_start and self.scheduled_end and self.scheduled_end < self.scheduled_start:
            raise ValueError("scheduled_end must not be before scheduled_start")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        return self


class JourneyBookingRead(BaseModel):
    id: int
    journey_id: int
    kind: str
    provider: str
    reference: str | None
    details: str | None
    origin: str | None
    destination: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    timezone: str
    latest_acceptable_arrival: datetime | None
    price_amount: float | None
    currency: str
    status: str
    verification_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingDependencyCreate(BaseModel):
    downstream_booking_id: int = Field(gt=0)
    dependency_type: Literal["connection", "pickup", "check_in", "appointment", "other"] = (
        "connection"
    )


class BookingDependencyRead(BaseModel):
    id: int
    journey_id: int
    predecessor_booking_id: int
    downstream_booking_id: int
    dependency_type: str

    model_config = ConfigDict(from_attributes=True)


class DisruptionAnalysisRequest(BaseModel):
    journey_id: int = Field(gt=0)
    affected_booking_id: int = Field(gt=0)
    disruption_status: Literal["cancelled", "delayed"]
    delay_minutes: int | None = Field(default=None, ge=0, le=10080)

    @model_validator(mode="after")
    def validate_disruption_delay(self):
        if self.disruption_status == "delayed" and self.delay_minutes is None:
            raise ValueError("delay_minutes is required for delayed disruptions")
        if self.disruption_status == "cancelled" and self.delay_minutes is not None:
            raise ValueError("delay_minutes must be omitted for cancellations")
        return self
