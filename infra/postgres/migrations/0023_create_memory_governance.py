"""Create memory governance lifecycle tables.

Revision ID: 0023_create_memory_governance
Revises: 0022_create_risk_guardrail_approvals
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023_create_memory_governance"
down_revision: str | None = "0022_create_risk_guardrail_approvals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Create memory governance tables."""
    op.create_table(
        "aion_memory_governance_rules",
        sa.Column("governance_rule_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.Text(), nullable=False),
        sa.Column("memory_types", JSONB, nullable=False),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("sensitivity_levels", JSONB, nullable=False),
        sa.Column("conditions", JSONB, nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("name", "status", "rule_type", "action", "priority", "created_at"):
        op.create_index(
            f"ix_aion_memory_governance_rules_{column}",
            "aion_memory_governance_rules",
            [column],
        )

    op.create_table(
        "aion_memory_governance_decisions",
        sa.Column("governance_decision_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("memory_id", sa.Text(), nullable=True),
        sa.Column("rule_ids", JSONB, nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for column in ("trace_id", "memory_id", "decision", "created_at"):
        op.create_index(
            f"ix_aion_memory_governance_decisions_{column}",
            "aion_memory_governance_decisions",
            [column],
        )

    op.create_table(
        "aion_memory_decay_records",
        sa.Column("decay_id", sa.Text(), primary_key=True),
        sa.Column("memory_id", sa.Text(), nullable=False),
        sa.Column("previous_score", sa.Float(), nullable=False),
        sa.Column("new_score", sa.Float(), nullable=False),
        sa.Column("decay_reason", sa.Text(), nullable=False),
        sa.Column("factors", JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for column in ("memory_id", "new_score", "created_at"):
        op.create_index(
            f"ix_aion_memory_decay_records_{column}",
            "aion_memory_decay_records",
            [column],
        )

    op.create_table(
        "aion_memory_forgetting_requests",
        sa.Column("forget_request_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("risk_assessment_id", sa.Text(), nullable=True),
        sa.Column("approval_request_id", sa.Text(), nullable=True),
        sa.Column("result", JSONB, nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "trace_id",
        "actor_id",
        "workspace_id",
        "target_type",
        "target_id",
        "status",
        "approval_request_id",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_memory_forgetting_requests_{column}",
            "aion_memory_forgetting_requests",
            [column],
        )

    op.create_table(
        "aion_memory_conflicts",
        sa.Column("conflict_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("conflict_type", sa.Text(), nullable=False),
        sa.Column("memory_ids", JSONB, nullable=False),
        sa.Column("evidence_ids", JSONB, nullable=False),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detected_by", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("trace_id", "conflict_type", "severity", "status", "detected_by", "created_at"):
        op.create_index(f"ix_aion_memory_conflicts_{column}", "aion_memory_conflicts", [column])

    op.create_table(
        "aion_memory_compaction_runs",
        sa.Column("compaction_run_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("memory_types", JSONB, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_memory_ids", JSONB, nullable=False),
        sa.Column("output_memory_ids", JSONB, nullable=False),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("result", JSONB, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("trace_id", "actor_id", "workspace_id", "status", "strategy", "created_at"):
        op.create_index(
            f"ix_aion_memory_compaction_runs_{column}",
            "aion_memory_compaction_runs",
            [column],
        )

    op.create_table(
        "aion_memory_compacted_records",
        sa.Column("compacted_record_id", sa.Text(), primary_key=True),
        sa.Column(
            "compaction_run_id",
            sa.Text(),
            sa.ForeignKey("aion_memory_compaction_runs.compaction_run_id"),
            nullable=False,
        ),
        sa.Column("output_memory_id", sa.Text(), nullable=False),
        sa.Column("input_memory_ids", JSONB, nullable=False),
        sa.Column("compaction_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for column in (
        "compaction_run_id",
        "output_memory_id",
        "compaction_type",
        "confidence",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_memory_compacted_records_{column}",
            "aion_memory_compacted_records",
            [column],
        )


def downgrade() -> None:
    """Drop memory governance tables."""
    op.drop_table("aion_memory_compacted_records")
    op.drop_table("aion_memory_compaction_runs")
    op.drop_table("aion_memory_conflicts")
    op.drop_table("aion_memory_forgetting_requests")
    op.drop_table("aion_memory_decay_records")
    op.drop_table("aion_memory_governance_decisions")
    op.drop_table("aion_memory_governance_rules")
