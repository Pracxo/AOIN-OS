"""Create runtime configuration control-plane tables."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0039_create_runtime_config"
down_revision = "0038_create_security_baseline"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "aion_config_profiles",
        sa.Column("config_profile_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("profile_type", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("values", jsonb, nullable=False),
        sa.Column("feature_flags", jsonb, nullable=False),
        sa.Column("constraints", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_aion_config_profiles_name"),
    )
    _indexes(
        "aion_config_profiles",
        ("name", "status", "profile_type", "created_at"),
    )

    op.create_table(
        "aion_config_values",
        sa.Column("config_value_id", sa.Text(), primary_key=True),
        sa.Column("config_key", sa.Text(), nullable=False),
        sa.Column("config_value", jsonb, nullable=False),
        sa.Column("value_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("sensitive", sa.Boolean(), nullable=False),
        sa.Column("mutable", sa.Boolean(), nullable=False),
        sa.Column("requires_restart", sa.Boolean(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("config_key", "source", name="uq_aion_config_values_key_source"),
    )
    _indexes(
        "aion_config_values",
        (
            "config_key",
            "value_type",
            "source",
            "status",
            "sensitive",
            "mutable",
            "requires_restart",
            "created_at",
        ),
    )

    op.create_table(
        "aion_feature_flag_overrides",
        sa.Column("feature_override_id", sa.Text(), primary_key=True),
        sa.Column("feature_key", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_feature_flag_overrides",
        (
            "feature_key",
            "enabled",
            "source",
            "status",
            "actor_id",
            "workspace_id",
            "expires_at",
            "created_at",
        ),
    )

    op.create_table(
        "aion_config_snapshots",
        sa.Column("config_snapshot_id", sa.Text(), primary_key=True),
        sa.Column("snapshot_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("settings", jsonb, nullable=False),
        sa.Column("feature_flags", jsonb, nullable=False),
        sa.Column("adapter_status", jsonb, nullable=False),
        sa.Column("config_hash", sa.Text(), nullable=False),
        sa.Column("drift_from_snapshot_id", sa.Text(), nullable=True),
        sa.Column("drift", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    _indexes(
        "aion_config_snapshots",
        ("snapshot_type", "status", "config_hash", "drift_from_snapshot_id", "created_at"),
    )

    op.create_table(
        "aion_config_validation_runs",
        sa.Column("config_validation_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("profile_id", sa.Text(), nullable=True),
        sa.Column("snapshot_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("checks", jsonb, nullable=False),
        sa.Column("failures", jsonb, nullable=False),
        sa.Column("warnings", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    _indexes(
        "aion_config_validation_runs",
        ("trace_id", "profile_id", "snapshot_id", "status", "created_at"),
    )

    op.create_table(
        "aion_config_change_records",
        sa.Column("config_change_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("change_type", sa.Text(), nullable=False),
        sa.Column("before", jsonb, nullable=False),
        sa.Column("after", jsonb, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("policy_decision_id", sa.Text(), nullable=True),
        sa.Column("risk_assessment_id", sa.Text(), nullable=True),
        sa.Column("approval_request_id", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    _indexes(
        "aion_config_change_records",
        ("trace_id", "actor_id", "workspace_id", "target_type", "target_id", "change_type"),
    )
    op.create_index(
        "ix_aion_config_change_records_created_at",
        "aion_config_change_records",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("aion_config_change_records")
    op.drop_table("aion_config_validation_runs")
    op.drop_table("aion_config_snapshots")
    op.drop_table("aion_feature_flag_overrides")
    op.drop_table("aion_config_values")
    op.drop_table("aion_config_profiles")


def _indexes(table_name: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table_name}_{column}", table_name, [column])
