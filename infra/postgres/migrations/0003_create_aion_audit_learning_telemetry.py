"""Create AION audit, evaluation, learning, and telemetry tables.

Revision ID: 0003_create_aion_audit_learning_telemetry
Revises: 0002_create_aion_memory_records
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_create_aion_audit_learning_telemetry"
down_revision: str | None = "0002_create_aion_memory_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create audit, evaluation, learning, and telemetry tables."""
    op.create_table(
        "aion_decision_traces",
        sa.Column("trace_id", sa.Text(), primary_key=True),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("intent_id", sa.Text(), nullable=True),
        sa.Column("context_id", sa.Text(), nullable=True),
        sa.Column("plan_id", sa.Text(), nullable=True),
        sa.Column("memory_refs", postgresql.JSONB(), nullable=False),
        sa.Column("capability_refs", postgresql.JSONB(), nullable=False),
        sa.Column("policy_decisions", postgresql.JSONB(), nullable=False),
        sa.Column("outcome", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aion_decision_traces_event_id", "aion_decision_traces", ["event_id"])
    op.create_index("ix_aion_decision_traces_created_at", "aion_decision_traces", ["created_at"])

    op.create_table(
        "aion_policy_decisions",
        sa.Column("decision_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("decision", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_aion_policy_decisions_trace_id", "aion_policy_decisions", ["trace_id"])

    op.create_table(
        "aion_learning_signals",
        sa.Column("learning_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("learning_type", sa.Text(), nullable=False),
        sa.Column("signal", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Double(), nullable=False),
        sa.Column("promotion_status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aion_learning_signals_trace_id", "aion_learning_signals", ["trace_id"])

    op.create_table(
        "aion_evaluations",
        sa.Column("evaluation_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("scores", postgresql.JSONB(), nullable=False),
        sa.Column("lessons", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_aion_evaluations_trace_id", "aion_evaluations", ["trace_id"])

    op.create_table(
        "aion_visual_telemetry",
        sa.Column("telemetry_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("node_type", sa.Text(), nullable=False),
        sa.Column("node_id", sa.Text(), nullable=False),
        sa.Column("edge_from", sa.Text(), nullable=True),
        sa.Column("edge_to", sa.Text(), nullable=True),
        sa.Column("intensity", sa.Double(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_aion_visual_telemetry_trace_id", "aion_visual_telemetry", ["trace_id"])
    op.create_index("ix_aion_visual_telemetry_event_type", "aion_visual_telemetry", ["event_type"])


def downgrade() -> None:
    """Drop audit, evaluation, learning, and telemetry tables."""
    op.drop_index("ix_aion_visual_telemetry_event_type", table_name="aion_visual_telemetry")
    op.drop_index("ix_aion_visual_telemetry_trace_id", table_name="aion_visual_telemetry")
    op.drop_table("aion_visual_telemetry")
    op.drop_index("ix_aion_evaluations_trace_id", table_name="aion_evaluations")
    op.drop_table("aion_evaluations")
    op.drop_index("ix_aion_learning_signals_trace_id", table_name="aion_learning_signals")
    op.drop_table("aion_learning_signals")
    op.drop_index("ix_aion_policy_decisions_trace_id", table_name="aion_policy_decisions")
    op.drop_table("aion_policy_decisions")
    op.drop_index("ix_aion_decision_traces_created_at", table_name="aion_decision_traces")
    op.drop_index("ix_aion_decision_traces_event_id", table_name="aion_decision_traces")
    op.drop_table("aion_decision_traces")
