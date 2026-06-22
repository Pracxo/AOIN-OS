"""Create visual projection and observability tables.

Revision ID: 0014_create_visual_projection_observability
Revises: 0013_create_evidence_vault
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014_create_visual_projection_observability"
down_revision = "0013_create_evidence_vault"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create visual projection and observability tables."""
    op.create_table(
        "aion_brain_map_snapshots",
        sa.Column("snapshot_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("owner_scope", _jsonb(), nullable=False),
        sa.Column("map", _jsonb(), nullable=False),
        sa.Column("node_count", sa.Integer(), nullable=False),
        sa.Column("edge_count", sa.Integer(), nullable=False),
        sa.Column("pulse_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aion_brain_map_snapshots_trace_id", "aion_brain_map_snapshots", ["trace_id"])
    op.create_index(
        "ix_aion_brain_map_snapshots_workspace_id",
        "aion_brain_map_snapshots",
        ["workspace_id"],
    )
    op.create_index(
        "ix_aion_brain_map_snapshots_created_at",
        "aion_brain_map_snapshots",
        ["created_at"],
    )

    op.create_table(
        "aion_observability_events",
        sa.Column("observability_event_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("component", sa.Text(), nullable=False),
        sa.Column("level", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("trace_id", "correlation_id", "event_type", "component", "level", "created_at"):
        op.create_index(f"ix_aion_observability_events_{column}", "aion_observability_events", [column])

    op.create_table(
        "aion_trace_timeline_records",
        sa.Column("timeline_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("owner_scope", _jsonb(), nullable=False),
        sa.Column("events", _jsonb(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("trace_id", "status", "created_at"):
        op.create_index(f"ix_aion_trace_timeline_records_{column}", "aion_trace_timeline_records", [column])


def downgrade() -> None:
    """Drop visual projection and observability tables."""
    op.drop_table("aion_trace_timeline_records")
    op.drop_table("aion_observability_events")
    op.drop_table("aion_brain_map_snapshots")
