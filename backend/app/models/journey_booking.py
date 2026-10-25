from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base


class JourneyBooking(Base):
    __tablename__ = "journey_bookings"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(30), nullable=False)
    provider = Column(String(120), nullable=False)
    reference = Column(String(80), nullable=True)
    details = Column(Text, nullable=True)
    origin = Column(String(120), nullable=True)
    destination = Column(String(120), nullable=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String(80), nullable=False, default="UTC", server_default="UTC")
    latest_acceptable_arrival = Column(DateTime(timezone=True), nullable=True)
    price_amount = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default="INR", server_default="INR")
    status = Column(String(30), nullable=False, default="scheduled", server_default="scheduled")
    verification_status = Column(
        String(30),
        nullable=False,
        default="USER_REPORTED",
        server_default="USER_REPORTED",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    journey = relationship("Journey", back_populates="bookings")
