"""Persist recovery plans and track fare/budget currencies."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261021_0005"
down_revision: Union[str, None] = "20261021_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "journeys",
        sa.Column(
            "budget_currency",
            sa.String(length=3),
            server_default="INR",
            nullable=False,
        ),
    )
    op.add_column(
        "alternatives",
        sa.Column(
            "currency",
            sa.String(length=3),
            server_default="INR",
            nullable=False,
        ),
    )
    op.create_table(
        "recovery_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journey_id", sa.Integer(), nullable=False),
        sa.Column("source_label", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["journey_id"],
            ["journeys.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recovery_plans_journey_id",
        "recovery_plans",
        ["journey_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_recovery_plans_journey_id", table_name="recovery_plans")
    op.drop_table("recovery_plans")
    op.drop_column("alternatives", "currency")
    op.drop_column("journeys", "budget_currency")
