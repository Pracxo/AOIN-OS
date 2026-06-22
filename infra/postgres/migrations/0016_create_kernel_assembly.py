"""Create kernel assembly, service registry, and self-test tables.

Revision ID: 0016_create_kernel_assembly
Revises: 0015_create_cognitive_replay_regression
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0016_create_kernel_assembly"
down_revision = "0015_create_cognitive_replay_regression"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create kernel lifecycle tables."""
    op.create_table(
        "aion_kernel_boot_records",
        sa.Column("boot_id", sa.Text(), primary_key=True),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("env", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("adapter_config", _jsonb(), nullable=False),
        sa.Column("diagnostics", _jsonb(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("service_name", "version", "env", "status", "started_at"):
        op.create_index(
            f"ix_aion_kernel_boot_records_{column}",
            "aion_kernel_boot_records",
            [column],
        )

    op.create_table(
        "aion_kernel_service_records",
        sa.Column("service_record_id", sa.Text(), primary_key=True),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("service_type", sa.Text(), nullable=False),
        sa.Column("adapter_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("health", _jsonb(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
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
    for column in ("service_name", "service_type", "adapter_name", "status", "created_at"):
        op.create_index(
            f"ix_aion_kernel_service_records_{column}",
            "aion_kernel_service_records",
            [column],
        )

    op.create_table(
        "aion_kernel_self_test_runs",
        sa.Column("self_test_id", sa.Text(), primary_key=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("checks", _jsonb(), nullable=False),
        sa.Column("report", _jsonb(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("status", "created_at"):
        op.create_index(
            f"ix_aion_kernel_self_test_runs_{column}",
            "aion_kernel_self_test_runs",
            [column],
        )


def downgrade() -> None:
    """Drop kernel lifecycle tables."""
    op.drop_table("aion_kernel_self_test_runs")
    op.drop_table("aion_kernel_service_records")
    op.drop_table("aion_kernel_boot_records")
