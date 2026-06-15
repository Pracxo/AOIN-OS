"""Create reflection and skill registry tables.

Revision ID: 0011_create_reflection_skill_registry
Revises: 0010_create_aion_lifecycle_control_plane
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011_create_reflection_skill_registry"
down_revision: str | None = "0010_create_aion_lifecycle_control_plane"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create reflection and skill registry tables."""
    op.create_table(
        "aion_reflections",
        sa.Column("reflection_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("task_id", sa.Text(), nullable=True),
        sa.Column("task_run_id", sa.Text(), nullable=True),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("evaluation_id", sa.Text(), nullable=True),
        sa.Column("learning_signal_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reflection_type", sa.Text(), nullable=False),
        sa.Column("observations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("proposed_changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in (
        "trace_id",
        "task_id",
        "task_run_id",
        "execution_id",
        "evaluation_id",
        "reflection_type",
        "status",
        "created_at",
    ):
        op.create_index(f"ix_aion_reflections_{column}", "aion_reflections", [column])

    op.create_table(
        "aion_skill_candidates",
        sa.Column("candidate_id", sa.Text(), primary_key=True),
        sa.Column("reflection_id", sa.Text(), nullable=True),
        sa.Column("source_trace_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_task_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_learning_signal_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("trigger_patterns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preconditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("procedure_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected_outcomes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evaluation_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("reflection_id", "name", "risk_level", "confidence", "status", "created_at"):
        op.create_index(f"ix_aion_skill_candidates_{column}", "aion_skill_candidates", [column])

    op.create_table(
        "aion_skills",
        sa.Column("skill_id", sa.Text(), primary_key=True),
        sa.Column("candidate_id", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("trigger_patterns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preconditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("procedure_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected_outcomes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "candidate_id",
        "name",
        "status",
        "risk_level",
        "current_version",
        "created_at",
    ):
        op.create_index(f"ix_aion_skills_{column}", "aion_skills", [column])

    op.create_table(
        "aion_skill_versions",
        sa.Column("skill_version_id", sa.Text(), primary_key=True),
        sa.Column("skill_id", sa.Text(), sa.ForeignKey("aion_skills.skill_id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("trigger_patterns", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preconditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("procedure_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected_outcomes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("source_candidate_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("skill_id", "version", "source_candidate_id", "created_at"):
        op.create_index(f"ix_aion_skill_versions_{column}", "aion_skill_versions", [column])

    op.create_table(
        "aion_skill_activation_events",
        sa.Column("activation_event_id", sa.Text(), primary_key=True),
        sa.Column("skill_id", sa.Text(), nullable=False),
        sa.Column("skill_version_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in (
        "skill_id",
        "skill_version_id",
        "trace_id",
        "event_type",
        "from_status",
        "to_status",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_skill_activation_events_{column}",
            "aion_skill_activation_events",
            [column],
        )


def downgrade() -> None:
    """Drop reflection and skill registry tables."""
    op.drop_table("aion_skill_activation_events")
    op.drop_table("aion_skill_versions")
    op.drop_table("aion_skills")
    op.drop_table("aion_skill_candidates")
    op.drop_table("aion_reflections")
