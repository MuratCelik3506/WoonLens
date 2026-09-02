"""Create named saved-comparison recipes.

Revision ID: 20260902_03
Revises: 20260902_02
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_03"
down_revision: str | None = "20260902_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_comparison",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["account.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_saved_comparison_account_id", "saved_comparison", ["account_id"]
    )
    op.create_table(
        "saved_comparison_address_reference",
        sa.Column("saved_comparison_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("pdok_address_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["saved_comparison_id"], ["saved_comparison.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("saved_comparison_id", "position"),
        sa.UniqueConstraint(
            "saved_comparison_id",
            "pdok_address_id",
            name="uq_saved_comparison_address",
        ),
        sa.CheckConstraint("position >= 0 AND position <= 4", name="ck_saved_position"),
    )


def downgrade() -> None:
    op.drop_table("saved_comparison_address_reference")
    op.drop_index("ix_saved_comparison_account_id", table_name="saved_comparison")
    op.drop_table("saved_comparison")
