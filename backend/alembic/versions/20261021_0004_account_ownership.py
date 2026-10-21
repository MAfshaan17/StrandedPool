"""Add owner IDs for account-scoped journeys and disruption reports."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261021_0004"
down_revision: Union[str, None] = "20261021_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("journeys") as batch_op:
        batch_op.add_column(sa.Column("owner_user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_journeys_owner_user_id_users",
            "users",
            ["owner_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
    op.create_index("ix_journeys_owner_user_id", "journeys", ["owner_user_id"])
    with op.batch_alter_table("disruptions") as batch_op:
        batch_op.add_column(sa.Column("reporter_user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_disruptions_reporter_user_id_users",
            "users",
            ["reporter_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
    op.create_index(
        "ix_disruptions_reporter_user_id",
        "disruptions",
        ["reporter_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_disruptions_reporter_user_id", table_name="disruptions")
    op.drop_column("disruptions", "reporter_user_id")
    op.drop_index("ix_journeys_owner_user_id", table_name="journeys")
    op.drop_column("journeys", "owner_user_id")
