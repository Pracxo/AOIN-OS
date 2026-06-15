"""Create scenario harness and release baseline tables."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0033_create_scenario_release_baseline"
down_revision = "0032_create_policy_catalog_permission_matrix"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "aion_scenario_definitions",
        sa.Column("scenario_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("scenario_type", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("steps", jsonb, nullable=False),
        sa.Column("expected", jsonb, nullable=False),
        sa.Column("tags", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_scenario_definitions_name", "aion_scenario_definitions", ["name"])
    op.create_index("ix_aion_scenario_definitions_status", "aion_scenario_definitions", ["status"])
    op.create_index(
        "ix_aion_scenario_definitions_scenario_type",
        "aion_scenario_definitions",
        ["scenario_type"],
    )
    op.create_index(
        "ix_aion_scenario_definitions_created_at",
        "aion_scenario_definitions",
        ["created_at"],
    )

    op.create_table(
        "aion_scenario_runs",
        sa.Column("scenario_run_id", sa.Text(), primary_key=True),
        sa.Column("scenario_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("passed_steps", sa.Integer(), nullable=False),
        sa.Column("failed_steps", sa.Integer(), nullable=False),
        sa.Column("skipped_steps", sa.Integer(), nullable=False),
        sa.Column("result", jsonb, nullable=False),
        sa.Column("comparison", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_scenario_runs_scenario_id", "aion_scenario_runs", ["scenario_id"])
    op.create_index("ix_aion_scenario_runs_trace_id", "aion_scenario_runs", ["trace_id"])
    op.create_index("ix_aion_scenario_runs_actor_id", "aion_scenario_runs", ["actor_id"])
    op.create_index("ix_aion_scenario_runs_workspace_id", "aion_scenario_runs", ["workspace_id"])
    op.create_index("ix_aion_scenario_runs_status", "aion_scenario_runs", ["status"])
    op.create_index("ix_aion_scenario_runs_mode", "aion_scenario_runs", ["mode"])
    op.create_index("ix_aion_scenario_runs_created_at", "aion_scenario_runs", ["created_at"])

    op.create_table(
        "aion_scenario_step_runs",
        sa.Column("scenario_step_run_id", sa.Text(), primary_key=True),
        sa.Column(
            "scenario_run_id",
            sa.Text(),
            sa.ForeignKey("aion_scenario_runs.scenario_run_id"),
            nullable=False,
        ),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("step_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input", jsonb, nullable=False),
        sa.Column("output", jsonb, nullable=False),
        sa.Column("expected", jsonb, nullable=False),
        sa.Column("error", jsonb, nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_aion_scenario_step_runs_scenario_run_id",
        "aion_scenario_step_runs",
        ["scenario_run_id"],
    )
    op.create_index("ix_aion_scenario_step_runs_step_id", "aion_scenario_step_runs", ["step_id"])
    op.create_index("ix_aion_scenario_step_runs_step_type", "aion_scenario_step_runs", ["step_type"])
    op.create_index("ix_aion_scenario_step_runs_status", "aion_scenario_step_runs", ["status"])
    op.create_index("ix_aion_scenario_step_runs_created_at", "aion_scenario_step_runs", ["created_at"])

    op.create_table(
        "aion_demo_fixture_records",
        sa.Column("fixture_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("fixture_type", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("content", jsonb, nullable=False),
        sa.Column("loaded", sa.Boolean(), nullable=False),
        sa.Column("result", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_demo_fixture_records_name", "aion_demo_fixture_records", ["name"])
    op.create_index("ix_aion_demo_fixture_records_status", "aion_demo_fixture_records", ["status"])
    op.create_index(
        "ix_aion_demo_fixture_records_fixture_type",
        "aion_demo_fixture_records",
        ["fixture_type"],
    )
    op.create_index("ix_aion_demo_fixture_records_loaded", "aion_demo_fixture_records", ["loaded"])
    op.create_index("ix_aion_demo_fixture_records_created_at", "aion_demo_fixture_records", ["created_at"])

    op.create_table(
        "aion_release_baseline_reports",
        sa.Column("release_baseline_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("scenario_run_ids", jsonb, nullable=False),
        sa.Column("quality_gate_results", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_release_baseline_reports_version", "aion_release_baseline_reports", ["version"])
    op.create_index("ix_aion_release_baseline_reports_status", "aion_release_baseline_reports", ["status"])
    op.create_index(
        "ix_aion_release_baseline_reports_created_at",
        "aion_release_baseline_reports",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("aion_release_baseline_reports")
    op.drop_table("aion_demo_fixture_records")
    op.drop_table("aion_scenario_step_runs")
    op.drop_table("aion_scenario_runs")
    op.drop_table("aion_scenario_definitions")
