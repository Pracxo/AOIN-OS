"""Create cognitive replay, snapshot, and regression tables.

Revision ID: 0015_create_cognitive_replay_regression
Revises: 0014_create_visual_projection_observability
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0015_create_cognitive_replay_regression"
down_revision = "0014_create_visual_projection_observability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create cognitive replay and regression tables."""
    op.create_table(
        "aion_brain_snapshots",
        sa.Column("snapshot_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("owner_scope", _jsonb(), nullable=False),
        sa.Column("snapshot_type", sa.Text(), nullable=False),
        sa.Column("state", _jsonb(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for column in ("trace_id", "workspace_id", "snapshot_type", "content_hash", "created_at"):
        op.create_index(f"ix_aion_brain_snapshots_{column}", "aion_brain_snapshots", [column])

    op.create_table(
        "aion_replay_runs",
        sa.Column("replay_id", sa.Text(), primary_key=True),
        sa.Column("source_trace_id", sa.Text(), nullable=False),
        sa.Column("replay_trace_id", sa.Text(), nullable=True),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_snapshot_id", sa.Text(), nullable=True),
        sa.Column("output_snapshot_id", sa.Text(), nullable=True),
        sa.Column("comparison", _jsonb(), nullable=False),
        sa.Column("drift_detected", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "source_trace_id",
        "replay_trace_id",
        "mode",
        "status",
        "drift_detected",
        "created_at",
    ):
        op.create_index(f"ix_aion_replay_runs_{column}", "aion_replay_runs", [column])

    op.create_table(
        "aion_regression_cases",
        sa.Column("case_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_trace_id", sa.Text(), nullable=False),
        sa.Column("input_snapshot_id", sa.Text(), nullable=False),
        sa.Column("expected_snapshot_id", sa.Text(), nullable=False),
        sa.Column("owner_scope", _jsonb(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("tags", _jsonb(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
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
    )
    for column in ("name", "source_trace_id", "status", "created_at"):
        op.create_index(f"ix_aion_regression_cases_{column}", "aion_regression_cases", [column])

    op.create_table(
        "aion_regression_runs",
        sa.Column("regression_run_id", sa.Text(), primary_key=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("drift_count", sa.Integer(), nullable=False),
        sa.Column("report", _jsonb(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("status", "created_at"):
        op.create_index(f"ix_aion_regression_runs_{column}", "aion_regression_runs", [column])

    op.create_table(
        "aion_regression_run_results",
        sa.Column("result_id", sa.Text(), primary_key=True),
        sa.Column(
            "regression_run_id",
            sa.Text(),
            sa.ForeignKey("aion_regression_runs.regression_run_id"),
            nullable=False,
        ),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("replay_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("drift_detected", sa.Boolean(), nullable=False),
        sa.Column("comparison", _jsonb(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for column in (
        "regression_run_id",
        "case_id",
        "replay_id",
        "status",
        "drift_detected",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_regression_run_results_{column}",
            "aion_regression_run_results",
            [column],
        )


def downgrade() -> None:
    """Drop cognitive replay and regression tables."""
    op.drop_table("aion_regression_run_results")
    op.drop_table("aion_regression_runs")
    op.drop_table("aion_regression_cases")
    op.drop_table("aion_replay_runs")
    op.drop_table("aion_brain_snapshots")
