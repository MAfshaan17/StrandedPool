from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    journey = relationship("Journey", back_populates="bookings")
