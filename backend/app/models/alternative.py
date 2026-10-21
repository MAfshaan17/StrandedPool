from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from .base import Base


class Alternative(Base):
    __tablename__ = "alternatives"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String(40), nullable=False)
    provider = Column(String(120), nullable=False)
    origin = Column(String(120), nullable=False)
    destination = Column(String(120), nullable=False)
    departure_at = Column(DateTime(timezone=True), nullable=True)
    arrival_at = Column(DateTime(timezone=True), nullable=True)
    fare_amount = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default="INR", server_default="INR")
    constraints_satisfied = Column(JSON, nullable=False, default=list)
    source_label = Column(String(80), nullable=False, default="Traveller-provided (unverified)")
    entered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    journey = relationship("Journey", back_populates="alternatives")
