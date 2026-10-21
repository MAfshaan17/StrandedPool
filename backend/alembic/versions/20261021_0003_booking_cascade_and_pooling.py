"""Add structured booking timing, dependency edges, and pooling consent."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261021_0003"
down_revision: Union[str, None] = "20261020_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "journeys",
        sa.Column("pooling_consent", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "journeys",
        sa.Column("passenger_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )

    op.add_column("journey_bookings", sa.Column("origin", sa.String(length=120)))
    op.add_column("journey_bookings", sa.Column("destination", sa.String(length=120)))
    op.add_column(
        "journey_bookings",
        sa.Column("scheduled_start", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "journey_bookings",
        sa.Column("scheduled_end", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "journey_bookings",
        sa.Column("timezone", sa.String(length=80), server_default="UTC", nullable=False),
    )
    op.add_column(
        "journey_bookings",
        sa.Column("latest_acceptable_arrival", sa.DateTime(timezone=True)),
    )
    op.add_column("journey_bookings", sa.Column("price_amount", sa.Float()))
    op.add_column(
        "journey_bookings",
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
    )
    op.add_column(
        "journey_bookings",
        sa.Column("status", sa.String(length=30), server_default="scheduled", nullable=False),
    )
    op.add_column(
        "journey_bookings",
        sa.Column(
            "verification_status",
            sa.String(length=30),
            server_default="USER_REPORTED",
            nullable=False,
        ),
    )

    op.create_table(
        "booking_dependencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journey_id", sa.Integer(), nullable=False),
        sa.Column("predecessor_booking_id", sa.Integer(), nullable=False),
        sa.Column("downstream_booking_id", sa.Integer(), nullable=False),
        sa.Column("dependency_type", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["journey_id"], ["journeys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["predecessor_booking_id"],
            ["journey_bookings.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["downstream_booking_id"],
            ["journey_bookings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "predecessor_booking_id",
            "downstream_booking_id",
            name="uq_booking_dependency_edge",
        ),
    )
    op.create_index(
        "ix_booking_dependencies_journey_id",
        "booking_dependencies",
        ["journey_id"],
    )
    op.create_index(
        "ix_booking_dependencies_predecessor_booking_id",
        "booking_dependencies",
        ["predecessor_booking_id"],
    )
    op.create_index(
        "ix_booking_dependencies_downstream_booking_id",
        "booking_dependencies",
        ["downstream_booking_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_dependencies_downstream_booking_id",
        table_name="booking_dependencies",
    )
    op.drop_index(
        "ix_booking_dependencies_predecessor_booking_id",
        table_name="booking_dependencies",
    )
    op.drop_index("ix_booking_dependencies_journey_id", table_name="booking_dependencies")
    op.drop_table("booking_dependencies")

    op.drop_column("journey_bookings", "verification_status")
    op.drop_column("journey_bookings", "status")
    op.drop_column("journey_bookings", "currency")
    op.drop_column("journey_bookings", "price_amount")
    op.drop_column("journey_bookings", "latest_acceptable_arrival")
    op.drop_column("journey_bookings", "timezone")
    op.drop_column("journey_bookings", "scheduled_end")
    op.drop_column("journey_bookings", "scheduled_start")
    op.drop_column("journey_bookings", "destination")
    op.drop_column("journey_bookings", "origin")
    op.drop_column("journeys", "passenger_count")
    op.drop_column("journeys", "pooling_consent")
