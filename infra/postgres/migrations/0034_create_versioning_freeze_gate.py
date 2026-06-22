"""Create versioning and freeze gate tables."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0034_create_versioning_freeze_gate"
down_revision = "0033_create_scenario_release_baseline"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "aion_version_manifests",
        sa.Column("version_manifest_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("release_channel", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("api_version", sa.Text(), nullable=False),
        sa.Column("sdk_version", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("contract_hash", sa.Text(), nullable=False),
        sa.Column("feature_flags", jsonb, nullable=False),
        sa.Column("adapter_matrix", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aion_version_manifests_version", "aion_version_manifests", ["version"])
    op.create_index(
        "ix_aion_version_manifests_release_channel",
        "aion_version_manifests",
        ["release_channel"],
    )
    op.create_index("ix_aion_version_manifests_status", "aion_version_manifests", ["status"])
    op.create_index(
        "ix_aion_version_manifests_api_version",
        "aion_version_manifests",
        ["api_version"],
    )
    op.create_index(
        "ix_aion_version_manifests_sdk_version",
        "aion_version_manifests",
        ["sdk_version"],
    )
    op.create_index(
        "ix_aion_version_manifests_schema_version",
        "aion_version_manifests",
        ["schema_version"],
    )
    op.create_index(
        "ix_aion_version_manifests_contract_hash",
        "aion_version_manifests",
        ["contract_hash"],
    )
    op.create_index(
        "ix_aion_version_manifests_created_at",
        "aion_version_manifests",
        ["created_at"],
    )

    op.create_table(
        "aion_feature_registry",
        sa.Column("feature_id", sa.Text(), primary_key=True),
        sa.Column("feature_key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("default_enabled", sa.Boolean(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("dependencies", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("feature_key", name="uq_aion_feature_registry_feature_key"),
    )
    op.create_index("ix_aion_feature_registry_feature_key", "aion_feature_registry", ["feature_key"])
    op.create_index("ix_aion_feature_registry_status", "aion_feature_registry", ["status"])
    op.create_index("ix_aion_feature_registry_category", "aion_feature_registry", ["category"])
    op.create_index(
        "ix_aion_feature_registry_default_enabled",
        "aion_feature_registry",
        ["default_enabled"],
    )
    op.create_index("ix_aion_feature_registry_required", "aion_feature_registry", ["required"])
    op.create_index("ix_aion_feature_registry_created_at", "aion_feature_registry", ["created_at"])

    op.create_table(
        "aion_compatibility_matrix_records",
        sa.Column("compatibility_matrix_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("api_version", sa.Text(), nullable=False),
        sa.Column("sdk_version", sa.Text(), nullable=False),
        sa.Column("python_version", sa.Text(), nullable=False),
        sa.Column("docker_compose_version", sa.Text(), nullable=True),
        sa.Column("postgres_version", sa.Text(), nullable=True),
        sa.Column("redis_version", sa.Text(), nullable=True),
        sa.Column("nats_version", sa.Text(), nullable=True),
        sa.Column("opa_version", sa.Text(), nullable=True),
        sa.Column("optional_adapters", jsonb, nullable=False),
        sa.Column("compatibility", jsonb, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_aion_compatibility_matrix_records_version",
        "aion_compatibility_matrix_records",
        ["version"],
    )
    op.create_index(
        "ix_aion_compatibility_matrix_records_api_version",
        "aion_compatibility_matrix_records",
        ["api_version"],
    )
    op.create_index(
        "ix_aion_compatibility_matrix_records_sdk_version",
        "aion_compatibility_matrix_records",
        ["sdk_version"],
    )
    op.create_index(
        "ix_aion_compatibility_matrix_records_python_version",
        "aion_compatibility_matrix_records",
        ["python_version"],
    )
    op.create_index(
        "ix_aion_compatibility_matrix_records_status",
        "aion_compatibility_matrix_records",
        ["status"],
    )
    op.create_index(
        "ix_aion_compatibility_matrix_records_created_at",
        "aion_compatibility_matrix_records",
        ["created_at"],
    )

    op.create_table(
        "aion_migration_baseline_records",
        sa.Column("migration_baseline_id", sa.Text(), primary_key=True),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("migration_count", sa.Integer(), nullable=False),
        sa.Column("migration_hash", sa.Text(), nullable=False),
        sa.Column("destructive_migrations", jsonb, nullable=False),
        sa.Column("tables", jsonb, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_aion_migration_baseline_records_schema_version",
        "aion_migration_baseline_records",
        ["schema_version"],
    )
    op.create_index(
        "ix_aion_migration_baseline_records_migration_hash",
        "aion_migration_baseline_records",
        ["migration_hash"],
    )
    op.create_index(
        "ix_aion_migration_baseline_records_status",
        "aion_migration_baseline_records",
        ["status"],
    )
    op.create_index(
        "ix_aion_migration_baseline_records_created_at",
        "aion_migration_baseline_records",
        ["created_at"],
    )

    op.create_table(
        "aion_release_artifact_manifests",
        sa.Column("release_artifact_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("artifacts", jsonb, nullable=False),
        sa.Column("checksums", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aion_release_artifact_manifests_version", "aion_release_artifact_manifests", ["version"])
    op.create_index("ix_aion_release_artifact_manifests_status", "aion_release_artifact_manifests", ["status"])
    op.create_index(
        "ix_aion_release_artifact_manifests_created_at",
        "aion_release_artifact_manifests",
        ["created_at"],
    )

    op.create_table(
        "aion_freeze_gate_runs",
        sa.Column("freeze_gate_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column("checks", jsonb, nullable=False),
        sa.Column("failures", jsonb, nullable=False),
        sa.Column("warnings", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_freeze_gate_runs_version", "aion_freeze_gate_runs", ["version"])
    op.create_index("ix_aion_freeze_gate_runs_status", "aion_freeze_gate_runs", ["status"])
    op.create_index("ix_aion_freeze_gate_runs_requested_by", "aion_freeze_gate_runs", ["requested_by"])
    op.create_index("ix_aion_freeze_gate_runs_created_at", "aion_freeze_gate_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("aion_freeze_gate_runs")
    op.drop_table("aion_release_artifact_manifests")
    op.drop_table("aion_migration_baseline_records")
    op.drop_table("aion_compatibility_matrix_records")
    op.drop_table("aion_feature_registry")
    op.drop_table("aion_version_manifests")
