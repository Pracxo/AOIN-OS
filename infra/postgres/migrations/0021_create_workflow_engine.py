"""Create durable workflow engine tables.

Revision ID: 0021_create_workflow_engine
Revises: 0020_create_mcp_adapter_metadata
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021_create_workflow_engine"
down_revision: str | None = "0020_create_mcp_adapter_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create workflow tables."""
    op.create_table(
        "aion_workflow_definitions",
        sa.Column("workflow_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trigger_type", sa.Text(), nullable=False),
        sa.Column("trigger_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("retry_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_workflow_definitions_name", "aion_workflow_definitions", ["name"])
    op.create_index("ix_aion_workflow_definitions_status", "aion_workflow_definitions", ["status"])
    op.create_index("ix_aion_workflow_definitions_trigger_type", "aion_workflow_definitions", ["trigger_type"])
    op.create_index("ix_aion_workflow_definitions_risk_level", "aion_workflow_definitions", ["risk_level"])
    op.create_index("ix_aion_workflow_definitions_created_by", "aion_workflow_definitions", ["created_by"])
    op.create_index("ix_aion_workflow_definitions_created_at", "aion_workflow_definitions", ["created_at"])

    op.create_table(
        "aion_workflow_runs",
        sa.Column("workflow_run_id", sa.Text(), primary_key=True),
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("task_id", sa.Text(), nullable=True),
        sa.Column("goal_id", sa.Text(), nullable=True),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("trigger_type", sa.Text(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in (
        "workflow_id",
        "trace_id",
        "task_id",
        "goal_id",
        "execution_id",
        "actor_id",
        "workspace_id",
        "status",
        "trigger_type",
        "next_retry_at",
        "created_at",
    ):
        op.create_index(f"ix_aion_workflow_runs_{column}", "aion_workflow_runs", [column])

    op.create_table(
        "aion_workflow_step_runs",
        sa.Column("workflow_step_run_id", sa.Text(), primary_key=True),
        sa.Column("workflow_run_id", sa.Text(), sa.ForeignKey("aion_workflow_runs.workflow_run_id"), nullable=False),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("workflow_run_id", "step_id", "action_type", "status", "attempt", "created_at"):
        op.create_index(f"ix_aion_workflow_step_runs_{column}", "aion_workflow_step_runs", [column])

    op.create_table(
        "aion_workflow_heartbeats",
        sa.Column("heartbeat_id", sa.Text(), primary_key=True),
        sa.Column("workflow_run_id", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("workflow_run_id", "worker_id", "status", "created_at"):
        op.create_index(f"ix_aion_workflow_heartbeats_{column}", "aion_workflow_heartbeats", [column])

    op.create_table(
        "aion_workflow_worker_records",
        sa.Column("worker_id", sa.Text(), primary_key=True),
        sa.Column("worker_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("worker_type", "status", "last_heartbeat_at", "created_at"):
        op.create_index(f"ix_aion_workflow_workers_{column}", "aion_workflow_worker_records", [column])

    op.create_table(
        "aion_workflow_events",
        sa.Column("workflow_event_id", sa.Text(), primary_key=True),
        sa.Column("workflow_id", sa.Text(), nullable=True),
        sa.Column("workflow_run_id", sa.Text(), nullable=True),
        sa.Column("step_run_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("workflow_id", "workflow_run_id", "step_run_id", "event_type", "from_status", "to_status", "created_at"):
        op.create_index(f"ix_aion_workflow_events_{column}", "aion_workflow_events", [column])


def downgrade() -> None:
    """Drop workflow tables."""
    op.drop_table("aion_workflow_events")
    op.drop_table("aion_workflow_worker_records")
    op.drop_table("aion_workflow_heartbeats")
    op.drop_table("aion_workflow_step_runs")
    op.drop_table("aion_workflow_runs")
    op.drop_table("aion_workflow_definitions")
