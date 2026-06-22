"""Create local release package tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0035_create_release_packages"
down_revision = "0034_create_versioning_freeze_gate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create release package and file ledgers."""
    op.create_table(
        "aion_release_packages",
        sa.Column("release_package_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("package_name", sa.Text(), nullable=False),
        sa.Column("package_path", sa.Text(), nullable=False),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("checksums", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("handoff_report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_release_packages_version", "aion_release_packages", ["version"])
    op.create_index("ix_aion_release_packages_status", "aion_release_packages", ["status"])
    op.create_index(
        "ix_aion_release_packages_package_name",
        "aion_release_packages",
        ["package_name"],
    )
    op.create_index(
        "ix_aion_release_packages_created_at",
        "aion_release_packages",
        ["created_at"],
    )
    op.create_table(
        "aion_release_package_files",
        sa.Column("release_package_file_id", sa.Text(), primary_key=True),
        sa.Column(
            "release_package_id",
            sa.Text(),
            sa.ForeignKey("aion_release_packages.release_package_id"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("artifact_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_aion_release_package_files_release_package_id",
        "aion_release_package_files",
        ["release_package_id"],
    )
    op.create_index(
        "ix_aion_release_package_files_artifact_type",
        "aion_release_package_files",
        ["artifact_type"],
    )
    op.create_index(
        "ix_aion_release_package_files_included",
        "aion_release_package_files",
        ["included"],
    )
    op.create_index(
        "ix_aion_release_package_files_sha256",
        "aion_release_package_files",
        ["sha256"],
    )
    op.create_index(
        "ix_aion_release_package_files_created_at",
        "aion_release_package_files",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop release package and file ledgers."""
    op.drop_index("ix_aion_release_package_files_created_at", "aion_release_package_files")
    op.drop_index("ix_aion_release_package_files_sha256", "aion_release_package_files")
    op.drop_index("ix_aion_release_package_files_included", "aion_release_package_files")
    op.drop_index("ix_aion_release_package_files_artifact_type", "aion_release_package_files")
    op.drop_index(
        "ix_aion_release_package_files_release_package_id",
        "aion_release_package_files",
    )
    op.drop_table("aion_release_package_files")
    op.drop_index("ix_aion_release_packages_created_at", "aion_release_packages")
    op.drop_index("ix_aion_release_packages_package_name", "aion_release_packages")
    op.drop_index("ix_aion_release_packages_status", "aion_release_packages")
    op.drop_index("ix_aion_release_packages_version", "aion_release_packages")
    op.drop_table("aion_release_packages")
