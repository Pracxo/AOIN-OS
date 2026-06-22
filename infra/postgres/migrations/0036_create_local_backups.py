"""Create local backup and restore-preview tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0036_create_local_backups"
down_revision = "0035_create_release_packages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create local backup ledgers."""
    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "aion_backup_jobs",
        sa.Column("backup_job_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("backup_type", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("resource_types", jsonb, nullable=False),
        sa.Column("redaction_mode", sa.Text(), nullable=False),
        sa.Column("output_dir", sa.Text(), nullable=False),
        sa.Column("manifest", jsonb, nullable=True),
        sa.Column("checksums", jsonb, nullable=False),
        sa.Column("result", jsonb, nullable=False),
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
        "trace_id",
        "actor_id",
        "workspace_id",
        "status",
        "backup_type",
        "redaction_mode",
        "created_at",
    ):
        op.create_index(f"ix_aion_backup_jobs_{column}", "aion_backup_jobs", [column])

    op.create_table(
        "aion_backup_files",
        sa.Column("backup_file_id", sa.Text(), primary_key=True),
        sa.Column(
            "backup_job_id",
            sa.Text(),
            sa.ForeignKey("aion_backup_jobs.backup_job_id"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for column in ("backup_job_id", "resource_type", "included", "sha256", "created_at"):
        op.create_index(f"ix_aion_backup_files_{column}", "aion_backup_files", [column])

    op.create_table(
        "aion_restore_previews",
        sa.Column("restore_preview_id", sa.Text(), primary_key=True),
        sa.Column("backup_job_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_manifest", jsonb, nullable=True),
        sa.Column("conflict_count", sa.Integer(), nullable=False),
        sa.Column("missing_dependency_count", sa.Integer(), nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("records_restorable", sa.Integer(), nullable=False),
        sa.Column("records_blocked", sa.Integer(), nullable=False),
        sa.Column("conflicts", jsonb, nullable=False),
        sa.Column("plan", jsonb, nullable=False),
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
        "backup_job_id",
        "trace_id",
        "actor_id",
        "workspace_id",
        "status",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_restore_previews_{column}",
            "aion_restore_previews",
            [column],
        )

    op.create_table(
        "aion_restore_jobs",
        sa.Column("restore_job_id", sa.Text(), primary_key=True),
        sa.Column("restore_preview_id", sa.Text(), nullable=False),
        sa.Column("backup_job_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("approval_request_id", sa.Text(), nullable=True),
        sa.Column("risk_assessment_id", sa.Text(), nullable=True),
        sa.Column("autonomy_decision_id", sa.Text(), nullable=True),
        sa.Column("result", jsonb, nullable=False),
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
        "restore_preview_id",
        "backup_job_id",
        "trace_id",
        "actor_id",
        "workspace_id",
        "status",
        "mode",
        "created_at",
    ):
        op.create_index(f"ix_aion_restore_jobs_{column}", "aion_restore_jobs", [column])


def downgrade() -> None:
    """Drop local backup ledgers."""
    for column in (
        "created_at",
        "mode",
        "status",
        "workspace_id",
        "actor_id",
        "trace_id",
        "backup_job_id",
        "restore_preview_id",
    ):
        op.drop_index(f"ix_aion_restore_jobs_{column}", "aion_restore_jobs")
    op.drop_table("aion_restore_jobs")
    for column in (
        "created_at",
        "status",
        "workspace_id",
        "actor_id",
        "trace_id",
        "backup_job_id",
    ):
        op.drop_index(f"ix_aion_restore_previews_{column}", "aion_restore_previews")
    op.drop_table("aion_restore_previews")
    for column in ("created_at", "sha256", "included", "resource_type", "backup_job_id"):
        op.drop_index(f"ix_aion_backup_files_{column}", "aion_backup_files")
    op.drop_table("aion_backup_files")
    for column in (
        "created_at",
        "redaction_mode",
        "backup_type",
        "status",
        "workspace_id",
        "actor_id",
        "trace_id",
    ):
        op.drop_index(f"ix_aion_backup_jobs_{column}", "aion_backup_jobs")
    op.drop_table("aion_backup_jobs")
