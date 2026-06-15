"""Create AION event ledger table.

Revision ID: 0001_create_aion_events
Revises:
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_aion_events"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the canonical AION event ledger."""
    op.create_table(
        "aion_events",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("payload_type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("security_scope", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_aion_events_event_type", "aion_events", ["event_type"])
    op.create_index("ix_aion_events_workspace_id", "aion_events", ["workspace_id"])
    op.create_index("ix_aion_events_trace_id", "aion_events", ["trace_id"])
    op.create_index("ix_aion_events_timestamp", "aion_events", ["timestamp"])
    op.create_index("ix_aion_events_correlation_id", "aion_events", ["correlation_id"])


def downgrade() -> None:
    """Drop the canonical AION event ledger."""
    op.drop_index("ix_aion_events_correlation_id", table_name="aion_events")
    op.drop_index("ix_aion_events_timestamp", table_name="aion_events")
    op.drop_index("ix_aion_events_trace_id", table_name="aion_events")
    op.drop_index("ix_aion_events_workspace_id", table_name="aion_events")
    op.drop_index("ix_aion_events_event_type", table_name="aion_events")
    op.drop_table("aion_events")
