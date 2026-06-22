"""Create AION context retrieval trace table.

Revision ID: 0006_create_aion_context_retrievals
Revises: 0005_create_aion_temporal_graph
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_create_aion_context_retrievals"
down_revision: str | None = "0005_create_aion_temporal_graph"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create context retrieval trace table."""
    op.create_table(
        "aion_context_retrievals",
        sa.Column("retrieval_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("intent_id", sa.Text(), nullable=True),
        sa.Column("context_id", sa.Text(), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("requested_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_aion_context_retrievals_trace_id", "aion_context_retrievals", ["trace_id"])
    op.create_index("ix_aion_context_retrievals_intent_id", "aion_context_retrievals", ["intent_id"])
    op.create_index(
        "ix_aion_context_retrievals_context_id",
        "aion_context_retrievals",
        ["context_id"],
    )
    op.create_index(
        "ix_aion_context_retrievals_created_at",
        "aion_context_retrievals",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop context retrieval trace table."""
    op.drop_index("ix_aion_context_retrievals_created_at", table_name="aion_context_retrievals")
    op.drop_index("ix_aion_context_retrievals_context_id", table_name="aion_context_retrievals")
    op.drop_index("ix_aion_context_retrievals_intent_id", table_name="aion_context_retrievals")
    op.drop_index("ix_aion_context_retrievals_trace_id", table_name="aion_context_retrievals")
    op.drop_table("aion_context_retrievals")
