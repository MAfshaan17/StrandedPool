from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base


class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    transport_mode = Column(String(40), nullable=True)
    status = Column(String(30), nullable=False, default="reported")
    source_label = Column(String(60), nullable=False, default="Traveller report (unverified)")
    reported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    journey = relationship("Journey", back_populates="disruptions")
