"""Create AION memory records table.

Revision ID: 0002_create_aion_memory_records
Revises: 0001_create_aion_events
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_create_aion_memory_records"
down_revision: str | None = "0001_create_aion_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the canonical AION memory table."""
    op.create_table(
        "aion_memory_records",
        sa.Column("memory_id", sa.Text(), primary_key=True),
        sa.Column("memory_type", sa.Text(), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(), nullable=False),
        sa.Column("source_event_id", sa.Text(), nullable=True),
        sa.Column("content_ref", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Double(), nullable=False),
        sa.Column("sensitivity", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_memory_records_memory_type", "aion_memory_records", ["memory_type"])
    op.create_index(
        "ix_aion_memory_records_source_event_id",
        "aion_memory_records",
        ["source_event_id"],
    )
    op.create_index("ix_aion_memory_records_created_at", "aion_memory_records", ["created_at"])
    op.create_index("ix_aion_memory_records_deleted_at", "aion_memory_records", ["deleted_at"])
    op.create_index(
        "ix_aion_memory_records_summary_fts",
        "aion_memory_records",
        [sa.text("to_tsvector('simple', summary)")],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Drop the canonical AION memory table."""
    op.drop_index("ix_aion_memory_records_summary_fts", table_name="aion_memory_records")
    op.drop_index("ix_aion_memory_records_deleted_at", table_name="aion_memory_records")
    op.drop_index("ix_aion_memory_records_created_at", table_name="aion_memory_records")
    op.drop_index("ix_aion_memory_records_source_event_id", table_name="aion_memory_records")
    op.drop_index("ix_aion_memory_records_memory_type", table_name="aion_memory_records")
    op.drop_table("aion_memory_records")
