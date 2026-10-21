from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from .base import Base


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    traveller_name = Column(String(80), nullable=False)
    origin = Column(String(120), nullable=False)
    destination = Column(String(120), nullable=False, index=True)
    departure_at = Column(DateTime(timezone=True), nullable=False, index=True)
    arrive_by = Column(DateTime(timezone=True), nullable=True)
    budget_amount = Column(Float, nullable=True)
    constraints = Column(JSON, nullable=False, default=list)
    pooling_consent = Column(Boolean, nullable=False, default=False, server_default="0")
    passenger_count = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    disruptions = relationship(
        "Disruption",
        back_populates="journey",
        cascade="all, delete-orphan",
    )
    alternatives = relationship(
        "Alternative",
        back_populates="journey",
        cascade="all, delete-orphan",
    )
    bookings = relationship(
        "JourneyBooking",
        back_populates="journey",
        cascade="all, delete-orphan",
    )
    owner = relationship("User", back_populates="journeys")
