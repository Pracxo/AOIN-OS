"""Create resilience control-plane tables.

Revision ID: 0040_create_resilience
Revises: 0039_create_runtime_config
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0040_create_resilience"
down_revision = "0039_create_runtime_config"
branch_labels = None
depends_on = None

jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "aion_dependency_health_records",
        sa.Column("dependency_health_id", sa.Text(), primary_key=True),
        sa.Column("dependency_name", sa.Text(), nullable=False),
        sa.Column("dependency_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("criticality", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("details", jsonb, nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    _indexes(
        "aion_dependency_health_records",
        ("dependency_name", "dependency_type", "status", "criticality", "checked_at"),
    )

    op.create_table(
        "aion_retry_policies",
        sa.Column("retry_policy_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("initial_delay_ms", sa.Integer(), nullable=False),
        sa.Column("max_delay_ms", sa.Integer(), nullable=False),
        sa.Column("backoff_multiplier", sa.Float(), nullable=False),
        sa.Column("jitter_enabled", sa.Boolean(), nullable=False),
        sa.Column("retryable_statuses", jsonb, nullable=False),
        sa.Column("non_retryable_statuses", jsonb, nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_aion_retry_policies_name"),
    )
    _indexes("aion_retry_policies", ("name", "status", "target_type", "created_at"))

    op.create_table(
        "aion_circuit_breakers",
        sa.Column("circuit_breaker_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("failure_threshold", sa.Integer(), nullable=False),
        sa.Column("recovery_timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("half_open_max_calls", sa.Integer(), nullable=False),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("half_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_aion_circuit_breakers_name"),
    )
    _indexes(
        "aion_circuit_breakers",
        ("name", "target_type", "target_id", "status", "opened_at", "created_at"),
    )

    op.create_table(
        "aion_degraded_mode_events",
        sa.Column("degraded_event_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("component", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("dependencies", jsonb, nullable=False),
        sa.Column("fallbacks_active", jsonb, nullable=False),
        sa.Column("constraints", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_degraded_mode_events",
        ("trace_id", "component", "status", "severity", "created_at", "resolved_at"),
    )

    op.create_table(
        "aion_fault_injection_rules",
        sa.Column("fault_rule_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("fault_type", sa.Text(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("constraints", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_fault_injection_rules",
        ("name", "status", "target_type", "target_id", "fault_type", "created_at"),
    )

    op.create_table(
        "aion_resilience_test_runs",
        sa.Column("resilience_test_run_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("fault_rule_ids", jsonb, nullable=False),
        sa.Column("checks", jsonb, nullable=False),
        sa.Column("failures", jsonb, nullable=False),
        sa.Column("warnings", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes("aion_resilience_test_runs", ("trace_id", "status", "mode", "created_at"))


def downgrade() -> None:
    op.drop_table("aion_resilience_test_runs")
    op.drop_table("aion_fault_injection_rules")
    op.drop_table("aion_degraded_mode_events")
    op.drop_table("aion_circuit_breakers")
    op.drop_table("aion_retry_policies")
    op.drop_table("aion_dependency_health_records")


def _indexes(table_name: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table_name}_{column}", table_name, [column])

