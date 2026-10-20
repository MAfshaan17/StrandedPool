"""Score traveller-entered constraint matches and clarify data timestamps.

Revision ID: 20261020_0002
Revises: 20261020_0001
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261020_0002"
down_revision: Union[str, None] = "20261020_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("alternatives") as batch_op:
        batch_op.alter_column(
            "data_checked_at",
            new_column_name="entered_at",
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        batch_op.add_column(
            sa.Column(
                "constraints_satisfied",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("alternatives") as batch_op:
        batch_op.drop_column("constraints_satisfied")
        batch_op.alter_column(
            "entered_at",
            new_column_name="data_checked_at",
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
