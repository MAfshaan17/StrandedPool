from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint

from .base import Base


class BookingDependency(Base):
    __tablename__ = "booking_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "predecessor_booking_id",
            "downstream_booking_id",
            name="uq_booking_dependency_edge",
        ),
    )

    id = Column(Integer, primary_key=True)
    journey_id = Column(
        Integer,
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predecessor_booking_id = Column(
        Integer,
        ForeignKey("journey_bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    downstream_booking_id = Column(
        Integer,
        ForeignKey("journey_bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dependency_type = Column(String(30), nullable=False, default="connection")
