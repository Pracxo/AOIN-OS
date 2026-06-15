"""Create AION goal and task lifecycle tables.

Revision ID: 0010_create_aion_lifecycle_control_plane
Revises: 0009_create_aion_module_bus
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010_create_aion_lifecycle_control_plane"
down_revision: str | None = "0009_create_aion_module_bus"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create goals, tasks, task runs, lifecycle events, and schedules."""
    op.create_table(
        "aion_goals",
        sa.Column("goal_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("success_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "trace_id",
        "actor_id",
        "workspace_id",
        "status",
        "priority",
        "risk_level",
        "created_at",
        "updated_at",
    ):
        op.create_index(f"ix_aion_goals_{column}", "aion_goals", [column])

    op.create_table(
        "aion_cognitive_tasks",
        sa.Column("task_id", sa.Text(), primary_key=True),
        sa.Column("goal_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("plan_id", sa.Text(), nullable=True),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "goal_id",
        "trace_id",
        "plan_id",
        "execution_id",
        "actor_id",
        "workspace_id",
        "task_type",
        "status",
        "priority",
        "risk_level",
        "due_at",
        "scheduled_for",
        "created_at",
    ):
        op.create_index(f"ix_aion_cognitive_tasks_{column}", "aion_cognitive_tasks", [column])

    op.create_table(
        "aion_task_runs",
        sa.Column("task_run_id", sa.Text(), primary_key=True),
        sa.Column(
            "task_id",
            sa.Text(),
            sa.ForeignKey("aion_cognitive_tasks.task_id"),
            nullable=False,
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("run_mode", sa.Text(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("task_id", "trace_id", "execution_id", "status", "run_mode", "created_at"):
        op.create_index(f"ix_aion_task_runs_{column}", "aion_task_runs", [column])

    op.create_table(
        "aion_task_lifecycle_events",
        sa.Column("lifecycle_event_id", sa.Text(), primary_key=True),
        sa.Column("task_id", sa.Text(), nullable=True),
        sa.Column("goal_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in (
        "task_id",
        "goal_id",
        "trace_id",
        "event_type",
        "from_status",
        "to_status",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_task_lifecycle_events_{column}",
            "aion_task_lifecycle_events",
            [column],
        )

    op.create_table(
        "aion_schedules",
        sa.Column("schedule_id", sa.Text(), primary_key=True),
        sa.Column("owner_type", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.Text(), nullable=False),
        sa.Column("schedule_type", sa.Text(), nullable=False),
        sa.Column("schedule_expression", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("owner_type", "owner_id", "schedule_type", "status", "next_run_at", "created_at"):
        op.create_index(f"ix_aion_schedules_{column}", "aion_schedules", [column])


def downgrade() -> None:
    """Drop goal and task lifecycle tables."""
    for column in ("created_at", "next_run_at", "status", "schedule_type", "owner_id", "owner_type"):
        op.drop_index(f"ix_aion_schedules_{column}", table_name="aion_schedules")
    op.drop_table("aion_schedules")
    for column in (
        "created_at",
        "to_status",
        "from_status",
        "event_type",
        "trace_id",
        "goal_id",
        "task_id",
    ):
        op.drop_index(
            f"ix_aion_task_lifecycle_events_{column}",
            table_name="aion_task_lifecycle_events",
        )
    op.drop_table("aion_task_lifecycle_events")
    for column in ("created_at", "run_mode", "status", "execution_id", "trace_id", "task_id"):
        op.drop_index(f"ix_aion_task_runs_{column}", table_name="aion_task_runs")
    op.drop_table("aion_task_runs")
    for column in (
        "created_at",
        "scheduled_for",
        "due_at",
        "risk_level",
        "priority",
        "status",
        "task_type",
        "workspace_id",
        "actor_id",
        "execution_id",
        "plan_id",
        "trace_id",
        "goal_id",
    ):
        op.drop_index(f"ix_aion_cognitive_tasks_{column}", table_name="aion_cognitive_tasks")
    op.drop_table("aion_cognitive_tasks")
    for column in (
        "updated_at",
        "created_at",
        "risk_level",
        "priority",
        "status",
        "workspace_id",
        "actor_id",
        "trace_id",
    ):
        op.drop_index(f"ix_aion_goals_{column}", table_name="aion_goals")
    op.drop_table("aion_goals")
