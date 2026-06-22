"""Create attention controller and working memory tables.

Revision ID: 0024_create_attention_working_memory
Revises: 0023_create_memory_governance
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024_create_attention_working_memory"
down_revision: str | None = "0023_create_memory_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Create attention and working memory tables."""
    op.create_table(
        "aion_focus_sessions",
        sa.Column("focus_session_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("focus_type", sa.Text(), nullable=False),
        sa.Column("active_goal_id", sa.Text(), nullable=True),
        sa.Column("active_task_id", sa.Text(), nullable=True),
        sa.Column("active_workflow_run_id", sa.Text(), nullable=True),
        sa.Column("active_trace_id", sa.Text(), nullable=True),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    _indexes(
        "aion_focus_sessions",
        (
            "trace_id",
            "actor_id",
            "workspace_id",
            "status",
            "focus_type",
            "active_goal_id",
            "active_task_id",
            "active_workflow_run_id",
            "created_at",
        ),
    )

    op.create_table(
        "aion_working_memory_slots",
        sa.Column("slot_id", sa.Text(), primary_key=True),
        sa.Column("focus_session_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("slot_type", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=True),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("priority", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("ttl_seconds", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_working_memory_slots",
        (
            "focus_session_id",
            "trace_id",
            "actor_id",
            "workspace_id",
            "slot_type",
            "source_type",
            "source_id",
            "priority",
            "expires_at",
            "pinned",
            "deleted_at",
            "created_at",
        ),
    )

    op.create_table(
        "aion_attention_signals",
        sa.Column("attention_signal_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("signal_type", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("urgency", sa.Float(), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_attention_signals",
        (
            "trace_id",
            "actor_id",
            "workspace_id",
            "signal_type",
            "source_type",
            "source_id",
            "urgency",
            "importance",
            "risk_level",
            "handled_at",
            "created_at",
        ),
    )

    op.create_table(
        "aion_attention_decisions",
        sa.Column("attention_decision_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("focus_session_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("decision_type", sa.Text(), nullable=False),
        sa.Column("selected_signal_ids", JSONB, nullable=False),
        sa.Column("selected_slot_ids", JSONB, nullable=False),
        sa.Column("selected_memory_ids", JSONB, nullable=False),
        sa.Column("selected_evidence_ids", JSONB, nullable=False),
        sa.Column("selected_skill_ids", JSONB, nullable=False),
        sa.Column("selected_capability_ids", JSONB, nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    _indexes(
        "aion_attention_decisions",
        (
            "trace_id",
            "focus_session_id",
            "actor_id",
            "workspace_id",
            "decision_type",
            "priority_score",
            "created_at",
        ),
    )

    op.create_table(
        "aion_context_budgets",
        sa.Column("context_budget_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("focus_session_id", sa.Text(), nullable=True),
        sa.Column("intent_id", sa.Text(), nullable=True),
        sa.Column("context_id", sa.Text(), nullable=True),
        sa.Column("max_items", sa.Integer(), nullable=False),
        sa.Column("max_chars", sa.Integer(), nullable=False),
        sa.Column("allocation", JSONB, nullable=False),
        sa.Column("used_items", sa.Integer(), nullable=False),
        sa.Column("used_chars", sa.Integer(), nullable=False),
        sa.Column("overflow_items", JSONB, nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    _indexes(
        "aion_context_budgets",
        ("trace_id", "focus_session_id", "intent_id", "context_id", "created_at"),
    )

    op.create_table(
        "aion_interrupt_records",
        sa.Column("interrupt_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("focus_session_id", sa.Text(), nullable=True),
        sa.Column("interrupt_type", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("decision", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_interrupt_records",
        (
            "trace_id",
            "actor_id",
            "workspace_id",
            "focus_session_id",
            "interrupt_type",
            "source_type",
            "source_id",
            "status",
            "priority_score",
            "created_at",
        ),
    )


def downgrade() -> None:
    """Drop attention and working memory tables."""
    op.drop_table("aion_interrupt_records")
    op.drop_table("aion_context_budgets")
    op.drop_table("aion_attention_decisions")
    op.drop_table("aion_attention_signals")
    op.drop_table("aion_working_memory_slots")
    op.drop_table("aion_focus_sessions")


def _indexes(table_name: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table_name}_{column}", table_name, [column])
