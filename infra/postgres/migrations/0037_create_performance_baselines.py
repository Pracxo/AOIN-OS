"""Create local performance benchmark tables."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0037_create_performance_baselines"
down_revision = "0036_create_local_backups"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "aion_performance_samples",
        sa.Column("performance_sample_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("benchmark_run_id", sa.Text(), nullable=True),
        sa.Column("operation_type", sa.Text(), nullable=False),
        sa.Column("component", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("input_size_bytes", sa.Integer(), nullable=True),
        sa.Column("output_size_bytes", sa.Integer(), nullable=True),
        sa.Column("item_count", sa.Integer(), nullable=True),
        sa.Column("error", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aion_performance_samples_benchmark_run_id", "aion_performance_samples", ["benchmark_run_id"])
    op.create_index("ix_aion_performance_samples_trace_id", "aion_performance_samples", ["trace_id"])
    op.create_index("ix_aion_performance_samples_operation_type", "aion_performance_samples", ["operation_type"])
    op.create_index("ix_aion_performance_samples_component", "aion_performance_samples", ["component"])
    op.create_index("ix_aion_performance_samples_status", "aion_performance_samples", ["status"])
    op.create_index("ix_aion_performance_samples_duration_ms", "aion_performance_samples", ["duration_ms"])
    op.create_index("ix_aion_performance_samples_created_at", "aion_performance_samples", ["created_at"])

    op.create_table(
        "aion_benchmark_definitions",
        sa.Column("benchmark_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("benchmark_type", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("steps", jsonb, nullable=False),
        sa.Column("thresholds", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_benchmark_definitions_name", "aion_benchmark_definitions", ["name"])
    op.create_index("ix_aion_benchmark_definitions_status", "aion_benchmark_definitions", ["status"])
    op.create_index("ix_aion_benchmark_definitions_benchmark_type", "aion_benchmark_definitions", ["benchmark_type"])
    op.create_index("ix_aion_benchmark_definitions_created_at", "aion_benchmark_definitions", ["created_at"])

    op.create_table(
        "aion_benchmark_runs",
        sa.Column("benchmark_run_id", sa.Text(), primary_key=True),
        sa.Column("benchmark_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("summary", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_benchmark_runs_benchmark_id", "aion_benchmark_runs", ["benchmark_id"])
    op.create_index("ix_aion_benchmark_runs_trace_id", "aion_benchmark_runs", ["trace_id"])
    op.create_index("ix_aion_benchmark_runs_actor_id", "aion_benchmark_runs", ["actor_id"])
    op.create_index("ix_aion_benchmark_runs_workspace_id", "aion_benchmark_runs", ["workspace_id"])
    op.create_index("ix_aion_benchmark_runs_status", "aion_benchmark_runs", ["status"])
    op.create_index("ix_aion_benchmark_runs_mode", "aion_benchmark_runs", ["mode"])
    op.create_index("ix_aion_benchmark_runs_created_at", "aion_benchmark_runs", ["created_at"])

    op.create_table(
        "aion_capacity_baselines",
        sa.Column("capacity_baseline_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("baseline_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("environment", jsonb, nullable=False),
        sa.Column("metrics", jsonb, nullable=False),
        sa.Column("thresholds", jsonb, nullable=False),
        sa.Column("benchmark_run_ids", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aion_capacity_baselines_version", "aion_capacity_baselines", ["version"])
    op.create_index("ix_aion_capacity_baselines_baseline_name", "aion_capacity_baselines", ["baseline_name"])
    op.create_index("ix_aion_capacity_baselines_status", "aion_capacity_baselines", ["status"])
    op.create_index("ix_aion_capacity_baselines_created_at", "aion_capacity_baselines", ["created_at"])

    op.create_table(
        "aion_resource_budget_profiles",
        sa.Column("resource_budget_profile_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("budgets", jsonb, nullable=False),
        sa.Column("enforcement_mode", sa.Text(), nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_resource_budget_profiles_name", "aion_resource_budget_profiles", ["name"])
    op.create_index("ix_aion_resource_budget_profiles_status", "aion_resource_budget_profiles", ["status"])
    op.create_index("ix_aion_resource_budget_profiles_enforcement_mode", "aion_resource_budget_profiles", ["enforcement_mode"])
    op.create_index("ix_aion_resource_budget_profiles_created_at", "aion_resource_budget_profiles", ["created_at"])

    op.create_table(
        "aion_performance_regression_reports",
        sa.Column("regression_report_id", sa.Text(), primary_key=True),
        sa.Column("baseline_id", sa.Text(), nullable=True),
        sa.Column("benchmark_run_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("regressions", jsonb, nullable=False),
        sa.Column("improvements", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aion_performance_regression_reports_baseline_id", "aion_performance_regression_reports", ["baseline_id"])
    op.create_index("ix_aion_performance_regression_reports_benchmark_run_id", "aion_performance_regression_reports", ["benchmark_run_id"])
    op.create_index("ix_aion_performance_regression_reports_status", "aion_performance_regression_reports", ["status"])
    op.create_index("ix_aion_performance_regression_reports_created_at", "aion_performance_regression_reports", ["created_at"])


def downgrade() -> None:
    op.drop_table("aion_performance_regression_reports")
    op.drop_table("aion_resource_budget_profiles")
    op.drop_table("aion_capacity_baselines")
    op.drop_table("aion_benchmark_runs")
    op.drop_table("aion_benchmark_definitions")
    op.drop_table("aion_performance_samples")
