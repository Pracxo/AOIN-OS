"""Create TurboVec index metadata tables.

Revision ID: 0018_create_turbovec_indexes
Revises: 0017_create_model_gateway
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0018_create_turbovec_indexes"
down_revision = "0017_create_model_gateway"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create TurboVec index metadata tables."""
    op.create_table(
        "aion_turbovec_indexes",
        sa.Column("index_id", sa.Text(), primary_key=True),
        sa.Column("index_name", sa.Text(), nullable=False),
        sa.Column("adapter_name", sa.Text(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("bit_width", sa.Integer(), nullable=False),
        sa.Column("index_path", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("rebuilt_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("index_name", "adapter_name", "status", "dimensions", "bit_width", "created_at"):
        op.create_index(f"ix_aion_turbovec_indexes_{column}", "aion_turbovec_indexes", [column])

    op.create_table(
        "aion_turbovec_index_entries",
        sa.Column("entry_id", sa.Text(), primary_key=True),
        sa.Column(
            "index_id",
            sa.Text(),
            sa.ForeignKey("aion_turbovec_indexes.index_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("memory_id", sa.Text(), nullable=False),
        sa.Column("vector_id", sa.BigInteger(), nullable=False),
        sa.Column("source_text_hash", sa.Text(), nullable=False),
        sa.Column("owner_scope", _jsonb(), nullable=False),
        sa.Column("memory_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("index_id", "memory_id", name="uq_aion_turbovec_entry_memory"),
        sa.UniqueConstraint("index_id", "vector_id", name="uq_aion_turbovec_entry_vector"),
    )
    for column in (
        "index_id",
        "memory_id",
        "vector_id",
        "source_text_hash",
        "memory_type",
        "status",
        "deleted_at",
    ):
        op.create_index(
            f"ix_aion_turbovec_index_entries_{column}",
            "aion_turbovec_index_entries",
            [column],
        )


def downgrade() -> None:
    """Drop TurboVec index metadata tables."""
    op.drop_table("aion_turbovec_index_entries")
    op.drop_table("aion_turbovec_indexes")
