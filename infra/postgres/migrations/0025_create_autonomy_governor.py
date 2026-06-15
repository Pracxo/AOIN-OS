"""Create autonomy governor tables.

Revision ID: 0025_create_autonomy_governor
Revises: 0024_create_attention_working_memory
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025_create_autonomy_governor"
down_revision: str | None = "0024_create_attention_working_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Create autonomy governor tables."""
    op.create_table(
        "aion_autonomy_profiles",
        sa.Column("autonomy_profile_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("default_mode", sa.Text(), nullable=False),
        sa.Column("max_mode", sa.Text(), nullable=False),
        sa.Column("max_risk_level", sa.Text(), nullable=False),
        sa.Column("allowed_action_types", JSONB, nullable=False),
        sa.Column("denied_action_types", JSONB, nullable=False),
        sa.Column("external_models_allowed", sa.Boolean(), nullable=False),
        sa.Column("external_tools_allowed", sa.Boolean(), nullable=False),
        sa.Column("background_workflows_allowed", sa.Boolean(), nullable=False),
        sa.Column("scheduler_allowed", sa.Boolean(), nullable=False),
        sa.Column("skill_promotion_allowed", sa.Boolean(), nullable=False),
        sa.Column("memory_forgetting_allowed", sa.Boolean(), nullable=False),
        sa.Column("approval_required_modes", JSONB, nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_autonomy_profiles",
        ("name", "status", "actor_id", "workspace_id", "default_mode", "max_mode", "max_risk_level", "created_at"),
    )

    op.create_table(
        "aion_run_level_records",
        sa.Column("run_level_id", sa.Text(), primary_key=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("active_profile_id", sa.Text(), nullable=True),
        sa.Column("run_level", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("set_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_run_level_records",
        ("actor_id", "workspace_id", "active_profile_id", "run_level", "status", "expires_at", "created_at"),
    )

    op.create_table(
        "aion_delegation_grants",
        sa.Column("delegation_id", sa.Text(), primary_key=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("delegated_by", sa.Text(), nullable=True),
        sa.Column("delegated_to", sa.Text(), nullable=True),
        sa.Column("owner_scope", JSONB, nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("max_risk_level", sa.Text(), nullable=False),
        sa.Column("allowed_action_types", JSONB, nullable=False),
        sa.Column("resource_types", JSONB, nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_delegation_grants",
        ("actor_id", "workspace_id", "delegated_by", "delegated_to", "mode", "max_risk_level", "status", "expires_at", "created_at"),
    )

    op.create_table(
        "aion_autonomy_decisions",
        sa.Column("autonomy_decision_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("requested_mode", sa.Text(), nullable=False),
        sa.Column("resolved_mode", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("allow", sa.Boolean(), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        sa.Column("delegation_id", sa.Text(), nullable=True),
        sa.Column("autonomy_profile_id", sa.Text(), nullable=True),
        sa.Column("run_level_id", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("constraints", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    _indexes(
        "aion_autonomy_decisions",
        ("trace_id", "actor_id", "workspace_id", "requested_mode", "resolved_mode", "action_type", "resource_type", "risk_level", "allow", "approval_required", "created_at"),
    )

    op.create_table(
        "aion_autonomy_lifecycle_events",
        sa.Column("autonomy_event_id", sa.Text(), primary_key=True),
        sa.Column("autonomy_profile_id", sa.Text(), nullable=True),
        sa.Column("run_level_id", sa.Text(), nullable=True),
        sa.Column("delegation_id", sa.Text(), nullable=True),
        sa.Column("autonomy_decision_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    _indexes(
        "aion_autonomy_lifecycle_events",
        ("autonomy_profile_id", "run_level_id", "delegation_id", "autonomy_decision_id", "trace_id", "event_type", "actor_id", "workspace_id", "created_at"),
    )


def downgrade() -> None:
    """Drop autonomy governor tables."""
    for table in (
        "aion_autonomy_lifecycle_events",
        "aion_autonomy_decisions",
        "aion_delegation_grants",
        "aion_run_level_records",
        "aion_autonomy_profiles",
    ):
        op.drop_table(table)


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])
