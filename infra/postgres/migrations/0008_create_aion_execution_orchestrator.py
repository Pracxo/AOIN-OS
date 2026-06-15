"""Create AION execution orchestrator tables.

Revision ID: 0008_create_aion_execution_orchestrator
Revises: 0007_create_aion_reasoning_mesh
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008_create_aion_execution_orchestrator"
down_revision: str | None = "0007_create_aion_reasoning_mesh"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create execution run, step, approval, and capability invocation tables."""
    op.add_column(
        "aion_decision_traces",
        sa.Column(
            "execution_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column("aion_decision_traces", "execution_refs", server_default=None)

    op.create_table(
        "aion_execution_runs",
        sa.Column("execution_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("plan_id", sa.Text(), nullable=False),
        sa.Column("intent_id", sa.Text(), nullable=True),
        sa.Column("context_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("trace_id", "plan_id", "intent_id", "context_id", "status", "workspace_id", "created_at"):
        op.create_index(f"ix_aion_execution_runs_{column}", "aion_execution_runs", [column])

    op.create_table(
        "aion_execution_steps",
        sa.Column("step_run_id", sa.Text(), primary_key=True),
        sa.Column(
            "execution_id",
            sa.Text(),
            sa.ForeignKey("aion_execution_runs.execution_id"),
            nullable=False,
        ),
        sa.Column("plan_id", sa.Text(), nullable=False),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("capability_required", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("policy_decision_id", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in (
        "execution_id",
        "plan_id",
        "step_id",
        "action_type",
        "capability_required",
        "risk_level",
        "status",
        "created_at",
    ):
        op.create_index(f"ix_aion_execution_steps_{column}", "aion_execution_steps", [column])

    op.create_table(
        "aion_approval_checkpoints",
        sa.Column("approval_id", sa.Text(), primary_key=True),
        sa.Column("execution_id", sa.Text(), nullable=False),
        sa.Column("step_run_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approval_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("execution_id", "step_run_id", "trace_id", "risk_level", "status", "created_at"):
        op.create_index(
            f"ix_aion_approval_checkpoints_{column}",
            "aion_approval_checkpoints",
            [column],
        )

    op.create_table(
        "aion_capability_invocation_records",
        sa.Column("invocation_id", sa.Text(), primary_key=True),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("step_run_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("policy_decision_id", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("execution_id", "step_run_id", "trace_id", "capability_id", "status", "created_at"):
        op.create_index(
            f"ix_aion_capability_invocation_records_{column}",
            "aion_capability_invocation_records",
            [column],
        )


def downgrade() -> None:
    """Drop execution orchestrator tables."""
    for column in ("created_at", "status", "capability_id", "trace_id", "step_run_id", "execution_id"):
        op.drop_index(
            f"ix_aion_capability_invocation_records_{column}",
            table_name="aion_capability_invocation_records",
        )
    op.drop_table("aion_capability_invocation_records")
    for column in ("created_at", "status", "risk_level", "trace_id", "step_run_id", "execution_id"):
        op.drop_index(
            f"ix_aion_approval_checkpoints_{column}",
            table_name="aion_approval_checkpoints",
        )
    op.drop_table("aion_approval_checkpoints")
    for column in (
        "created_at",
        "status",
        "risk_level",
        "capability_required",
        "action_type",
        "step_id",
        "plan_id",
        "execution_id",
    ):
        op.drop_index(f"ix_aion_execution_steps_{column}", table_name="aion_execution_steps")
    op.drop_table("aion_execution_steps")
    for column in ("created_at", "workspace_id", "status", "context_id", "intent_id", "plan_id", "trace_id"):
        op.drop_index(f"ix_aion_execution_runs_{column}", table_name="aion_execution_runs")
    op.drop_table("aion_execution_runs")
    op.drop_column("aion_decision_traces", "execution_refs")
