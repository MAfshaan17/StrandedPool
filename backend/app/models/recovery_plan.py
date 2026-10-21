from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func

from .base import Base


class RecoveryPlanRecord(Base):
    __tablename__ = "recovery_plans"

    id = Column(Integer, primary_key=True)
    journey_id = Column(
        Integer,
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_label = Column(String(120), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
