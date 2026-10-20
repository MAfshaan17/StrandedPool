"""Create the initial StrandedPool schema.

Revision ID: 20261020_0001
Revises:
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261020_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "traveller_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_traveller_profiles_id", "traveller_profiles", ["id"])
    op.create_index("ix_traveller_profiles_user_id", "traveller_profiles", ["user_id"])

    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("traveller_profile_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["traveller_profile_id"], ["traveller_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trips_id", "trips", ["id"])
    op.create_index("ix_trips_traveller_profile_id", "trips", ["traveller_profile_id"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_id", "bookings", ["id"])
    op.create_index("ix_bookings_trip_id", "bookings", ["trip_id"])

    op.create_table(
        "journeys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("traveller_name", sa.String(length=80), nullable=False),
        sa.Column("origin", sa.String(length=120), nullable=False),
        sa.Column("destination", sa.String(length=120), nullable=False),
        sa.Column("departure_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrive_by", sa.DateTime(timezone=True), nullable=True),
        sa.Column("budget_amount", sa.Float(), nullable=True),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_journeys_id", "journeys", ["id"])
    op.create_index("ix_journeys_destination", "journeys", ["destination"])
    op.create_index("ix_journeys_departure_at", "journeys", ["departure_at"])

    op.create_table(
        "journey_bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journey_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("reference", sa.String(length=80), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["journey_id"], ["journeys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_journey_bookings_id", "journey_bookings", ["id"])

    op.create_table(
        "disruptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journey_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("transport_mode", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source_label", sa.String(length=60), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["journey_id"], ["journeys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_disruptions_id", "disruptions", ["id"])

    op.create_table(
        "alternatives",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journey_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("origin", sa.String(length=120), nullable=False),
        sa.Column("destination", sa.String(length=120), nullable=False),
        sa.Column("departure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fare_amount", sa.Float(), nullable=True),
        sa.Column("source_label", sa.String(length=80), nullable=False),
        sa.Column("data_checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["journey_id"], ["journeys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alternatives_id", "alternatives", ["id"])


def downgrade() -> None:
    op.drop_index("ix_alternatives_id", table_name="alternatives")
    op.drop_table("alternatives")
    op.drop_index("ix_disruptions_id", table_name="disruptions")
    op.drop_table("disruptions")
    op.drop_index("ix_journey_bookings_id", table_name="journey_bookings")
    op.drop_table("journey_bookings")
    op.drop_index("ix_journeys_departure_at", table_name="journeys")
    op.drop_index("ix_journeys_destination", table_name="journeys")
    op.drop_index("ix_journeys_id", table_name="journeys")
    op.drop_table("journeys")
    op.drop_index("ix_bookings_trip_id", table_name="bookings")
    op.drop_index("ix_bookings_id", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_trips_traveller_profile_id", table_name="trips")
    op.drop_index("ix_trips_id", table_name="trips")
    op.drop_table("trips")
    op.drop_index("ix_traveller_profiles_user_id", table_name="traveller_profiles")
    op.drop_index("ix_traveller_profiles_id", table_name="traveller_profiles")
    op.drop_table("traveller_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
