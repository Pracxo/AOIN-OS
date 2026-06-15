"""Create model gateway provider, profile, budget, usage, and redaction tables.

Revision ID: 0017_create_model_gateway
Revises: 0016_create_kernel_assembly
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0017_create_model_gateway"
down_revision = "0016_create_kernel_assembly"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create model gateway tables."""
    op.create_table(
        "aion_model_providers",
        sa.Column("provider_id", sa.Text(), primary_key=True),
        sa.Column("provider_type", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("endpoint_ref", sa.Text(), nullable=True),
        sa.Column("config", _jsonb(), nullable=False),
        sa.Column("health_status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("provider_type", "status", "health_status", "created_at"):
        op.create_index(f"ix_aion_model_providers_{column}", "aion_model_providers", [column])

    op.create_table(
        "aion_model_profiles",
        sa.Column("model_profile_id", sa.Text(), primary_key=True),
        sa.Column("provider_id", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("privacy_level", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("max_input_tokens", sa.Integer(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_per_1k_input_tokens", sa.Double(), nullable=True),
        sa.Column("cost_per_1k_output_tokens", sa.Double(), nullable=True),
        sa.Column("latency_class", sa.Text(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in (
        "provider_id",
        "model_name",
        "mode",
        "status",
        "privacy_level",
        "risk_level",
        "latency_class",
        "created_at",
    ):
        op.create_index(f"ix_aion_model_profiles_{column}", "aion_model_profiles", [column])

    op.create_table(
        "aion_model_budget_records",
        sa.Column("budget_id", sa.Text(), primary_key=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("scope", _jsonb(), nullable=False),
        sa.Column("budget_type", sa.Text(), nullable=False),
        sa.Column("limit_amount", sa.Double(), nullable=False),
        sa.Column("used_amount", sa.Double(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("resets_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("workspace_id", "actor_id", "budget_type", "status", "resets_at", "created_at"):
        op.create_index(
            f"ix_aion_model_budget_records_{column}",
            "aion_model_budget_records",
            [column],
        )

    op.create_table(
        "aion_model_usage_records",
        sa.Column("usage_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("reasoning_id", sa.Text(), nullable=True),
        sa.Column("model_call_id", sa.Text(), nullable=True),
        sa.Column("provider_id", sa.Text(), nullable=False),
        sa.Column("model_profile_id", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("input_token_estimate", sa.Integer(), nullable=False),
        sa.Column("output_token_estimate", sa.Integer(), nullable=False),
        sa.Column("cost_estimate", sa.Double(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in (
        "trace_id",
        "reasoning_id",
        "model_call_id",
        "provider_id",
        "model_profile_id",
        "model_name",
        "mode",
        "status",
        "actor_id",
        "workspace_id",
        "created_at",
    ):
        op.create_index(f"ix_aion_model_usage_records_{column}", "aion_model_usage_records", [column])

    op.create_table(
        "aion_prompt_redaction_records",
        sa.Column("redaction_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("reasoning_id", sa.Text(), nullable=True),
        sa.Column("prompt_id", sa.Text(), nullable=True),
        sa.Column("redaction_count", sa.Integer(), nullable=False),
        sa.Column("redaction_types", _jsonb(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for column in ("trace_id", "reasoning_id", "prompt_id", "blocked", "created_at"):
        op.create_index(
            f"ix_aion_prompt_redaction_records_{column}",
            "aion_prompt_redaction_records",
            [column],
        )


def downgrade() -> None:
    """Drop model gateway tables."""
    op.drop_table("aion_prompt_redaction_records")
    op.drop_table("aion_model_usage_records")
    op.drop_table("aion_model_budget_records")
    op.drop_table("aion_model_profiles")
    op.drop_table("aion_model_providers")
