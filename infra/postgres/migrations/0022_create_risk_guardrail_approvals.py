"""Create risk, guardrail, and approval control-plane tables.

Revision ID: 0022_create_risk_guardrail_approvals
Revises: 0021_create_workflow_engine
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022_create_risk_guardrail_approvals"
down_revision: str | None = "0021_create_workflow_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Create control-plane tables."""
    op.create_table(
        "aion_risk_assessments",
        sa.Column("risk_assessment_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("requested_risk_level", sa.Text(), nullable=False),
        sa.Column("computed_risk_level", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("factors", JSONB, nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in (
        "trace_id",
        "actor_id",
        "workspace_id",
        "action_type",
        "resource_type",
        "resource_id",
        "computed_risk_level",
        "decision",
        "created_at",
    ):
        op.create_index(f"ix_aion_risk_assessments_{column}", "aion_risk_assessments", [column])

    op.create_table(
        "aion_guardrail_rules",
        sa.Column("guardrail_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("scope", JSONB, nullable=False),
        sa.Column("action_types", JSONB, nullable=False),
        sa.Column("resource_types", JSONB, nullable=False),
        sa.Column("risk_levels", JSONB, nullable=False),
        sa.Column("conditions", JSONB, nullable=False),
        sa.Column("effect", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("name", "status", "effect", "severity", "created_at"):
        op.create_index(f"ix_aion_guardrail_rules_{column}", "aion_guardrail_rules", [column])

    op.create_table(
        "aion_guardrail_decisions",
        sa.Column("guardrail_decision_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("risk_assessment_id", sa.Text(), nullable=True),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("matched_guardrails", JSONB, nullable=False),
        sa.Column("allow", sa.Boolean(), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in (
        "trace_id",
        "risk_assessment_id",
        "action_type",
        "resource_type",
        "allow",
        "approval_required",
        "blocked",
        "severity",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_guardrail_decisions_{column}",
            "aion_guardrail_decisions",
            [column],
        )

    op.create_table(
        "aion_approval_requests",
        sa.Column("approval_request_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.Text(), nullable=True),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_assessment_id", sa.Text(), nullable=True),
        sa.Column("guardrail_decision_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("approval_scope", JSONB, nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "trace_id",
        "actor_id",
        "workspace_id",
        "requested_by",
        "assigned_to",
        "action_type",
        "resource_type",
        "resource_id",
        "status",
        "priority",
        "expires_at",
        "created_at",
    ):
        op.create_index(f"ix_aion_approval_requests_{column}", "aion_approval_requests", [column])

    op.create_table(
        "aion_approval_decisions",
        sa.Column("approval_decision_id", sa.Text(), primary_key=True),
        sa.Column("approval_request_id", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.Text(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("decision_payload", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("approval_request_id", "trace_id", "decided_by", "decision", "created_at"):
        op.create_index(f"ix_aion_approval_decisions_{column}", "aion_approval_decisions", [column])

    op.create_table(
        "aion_approval_lifecycle_events",
        sa.Column("approval_event_id", sa.Text(), primary_key=True),
        sa.Column("approval_request_id", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("approval_request_id", "trace_id", "event_type", "actor_id", "created_at"):
        op.create_index(
            f"ix_aion_approval_lifecycle_events_{column}",
            "aion_approval_lifecycle_events",
            [column],
        )


def downgrade() -> None:
    """Drop control-plane tables."""
    op.drop_table("aion_approval_lifecycle_events")
    op.drop_table("aion_approval_decisions")
    op.drop_table("aion_approval_requests")
    op.drop_table("aion_guardrail_decisions")
    op.drop_table("aion_guardrail_rules")
    op.drop_table("aion_risk_assessments")
