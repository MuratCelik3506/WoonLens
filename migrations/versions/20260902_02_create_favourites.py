"""Create minimum favourite address references.

Revision ID: 20260902_02
Revises: 20260902_01
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_02"
down_revision: str | None = "20260902_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "favourite_address_reference",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("pdok_address_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["account.id"],
            name="fk_favourite_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_favourite_address_reference"),
        sa.UniqueConstraint(
            "account_id", "pdok_address_id", name="uq_favourite_owner_address"
        ),
    )
    op.create_index(
        "ix_favourite_address_reference_account_id",
        "favourite_address_reference",
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_favourite_address_reference_account_id",
        table_name="favourite_address_reference",
    )
    op.drop_table("favourite_address_reference")
