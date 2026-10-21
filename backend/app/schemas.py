from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _normalize_currency_code(value: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
        raise ValueError("Currency must be a three-letter ISO-style code.")
    return normalized


def _normalize_utc_timestamp(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a UTC offset")
    return value.astimezone(timezone.utc)


def _read_as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class JourneyCreate(BaseModel):
    traveller_name: str = Field(min_length=1, max_length=80)
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    departure_at: datetime
    arrive_by: datetime | None = None
    budget_amount: float | None = Field(default=None, ge=0)
    budget_currency: str = Field(default="INR", min_length=3, max_length=3)
    constraints: list[str] = Field(default_factory=list, max_length=12)
    pooling_consent: bool = False
    passenger_count: int = Field(default=1, ge=1, le=12)

    @field_validator("budget_currency")
    @classmethod
    def normalize_budget_currency(cls, value: str) -> str:
        return _normalize_currency_code(value)

    @model_validator(mode="after")
    def validate_journey_times(self):
        self.departure_at = _normalize_utc_timestamp(self.departure_at, "departure_at")
        self.arrive_by = _normalize_utc_timestamp(self.arrive_by, "arrive_by")
        if self.arrive_by and self.arrive_by < self.departure_at:
            raise ValueError("arrive_by must not be before departure_at")
        return self


class JourneyRead(BaseModel):
    id: int
    traveller_name: str
    origin: str
    destination: str
    departure_at: datetime
    arrive_by: datetime | None
    budget_amount: float | None
    budget_currency: str
    constraints: list[str]
    pooling_consent: bool
    passenger_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def normalize_persisted_times(self):
        self.departure_at = _read_as_utc(self.departure_at)
        self.arrive_by = _read_as_utc(self.arrive_by)
        return self


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
    currency: str = Field(default="INR", min_length=3, max_length=3)
    constraints_satisfied: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return _normalize_currency_code(value)

    @model_validator(mode="after")
    def validate_alternative_times(self):
        self.departure_at = _normalize_utc_timestamp(
            self.departure_at,
            "departure_at",
        )
        self.arrival_at = _normalize_utc_timestamp(self.arrival_at, "arrival_at")
        if (
            self.departure_at is not None
            and self.arrival_at is not None
            and self.arrival_at < self.departure_at
        ):
            raise ValueError("arrival_at must not be before departure_at")
        return self


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
    currency: str
    constraints_satisfied: list[str]
    source_label: str
    entered_at: datetime
    data_freshness: str
    score: int
    destination_match: bool
    within_budget: bool | None
    currency_compatible: bool
    arrives_on_time: bool | None
    feasible: bool
    rejected_reasons: list[str]
    score_breakdown: dict[str, float]
    reasons: list[str]

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def normalize_persisted_times(self):
        self.departure_at = _read_as_utc(self.departure_at)
        self.arrival_at = _read_as_utc(self.arrival_at)
        self.entered_at = _read_as_utc(self.entered_at)
        return self


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
            setattr(
                self,
                timestamp_name,
                _normalize_utc_timestamp(timestamp, timestamp_name),
            )
        if self.scheduled_start and self.scheduled_end and self.scheduled_end < self.scheduled_start:
            raise ValueError("scheduled_end must not be before scheduled_start")
        self.currency = _normalize_currency_code(self.currency)
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

    @model_validator(mode="after")
    def normalize_persisted_times(self):
        self.scheduled_start = _read_as_utc(self.scheduled_start)
        self.scheduled_end = _read_as_utc(self.scheduled_end)
        self.latest_acceptable_arrival = _read_as_utc(
            self.latest_acceptable_arrival
        )
        return self


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


class ActionDraftRequest(BaseModel):
    action: Literal[
        "hotel_late_checkin",
        "refund_inquiry",
        "cab_pickup_update",
        "appointment_reschedule",
        "disruption_notification",
    ]
    language: Literal["en", "hi", "kn"] = "en"
    provider_name: str = Field(min_length=1, max_length=120)
    origin: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)


class ActionDraftResponse(BaseModel):
    action: str
    language: str
    provider_name: str
    content: str
    source: Literal["StrandedPool editable template"] = "StrandedPool editable template"
    requires_user_review: Literal[True] = True
    sent: Literal[False] = False


class RecoveryGenerateRequest(BaseModel):
    journey_id: int = Field(gt=0)
    affected_booking_id: int | None = Field(default=None, gt=0)
    disruption_status: Literal["cancelled", "delayed"] | None = None
    delay_minutes: int | None = Field(default=None, ge=0, le=10080)
    selected_alternative_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_recovery_inputs(self):
        if (self.affected_booking_id is None) != (self.disruption_status is None):
            raise ValueError(
                "affected_booking_id and disruption_status must be provided together"
            )
        if self.disruption_status == "delayed" and self.delay_minutes is None:
            raise ValueError("delay_minutes is required for delayed disruptions")
        if self.disruption_status == "cancelled" and self.delay_minutes is not None:
            raise ValueError("delay_minutes must be omitted for cancellations")
        if self.disruption_status is None and self.delay_minutes is not None:
            raise ValueError("delay_minutes requires a disruption to analyze")
        return self
