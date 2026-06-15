"""Create AION module bus runtime tables.

Revision ID: 0009_create_aion_module_bus
Revises: 0008_create_aion_execution_orchestrator
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009_create_aion_module_bus"
down_revision: str | None = "0008_create_aion_execution_orchestrator"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create module runtimes, bindings, and health checks."""
    op.create_table(
        "aion_module_runtimes",
        sa.Column("runtime_id", sa.Text(), primary_key=True),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("runtime_type", sa.Text(), nullable=False),
        sa.Column("endpoint_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("health_status", sa.Text(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "module_id",
        "version",
        "runtime_type",
        "status",
        "health_status",
        "created_at",
    ):
        op.create_index(f"ix_aion_module_runtimes_{column}", "aion_module_runtimes", [column])

    op.create_table(
        "aion_capability_runtime_bindings",
        sa.Column("binding_id", sa.Text(), primary_key=True),
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("runtime_id", sa.Text(), nullable=False),
        sa.Column("invocation_mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in (
        "capability_id",
        "module_id",
        "runtime_id",
        "invocation_mode",
        "status",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_capability_runtime_bindings_{column}",
            "aion_capability_runtime_bindings",
            [column],
        )

    op.create_table(
        "aion_module_health_checks",
        sa.Column("health_check_id", sa.Text(), primary_key=True),
        sa.Column("runtime_id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("runtime_id", "module_id", "status", "created_at"):
        op.create_index(
            f"ix_aion_module_health_checks_{column}",
            "aion_module_health_checks",
            [column],
        )


def downgrade() -> None:
    """Drop module bus runtime tables."""
    for column in ("created_at", "status", "module_id", "runtime_id"):
        op.drop_index(
            f"ix_aion_module_health_checks_{column}",
            table_name="aion_module_health_checks",
        )
    op.drop_table("aion_module_health_checks")
    for column in (
        "created_at",
        "status",
        "invocation_mode",
        "runtime_id",
        "module_id",
        "capability_id",
    ):
        op.drop_index(
            f"ix_aion_capability_runtime_bindings_{column}",
            table_name="aion_capability_runtime_bindings",
        )
    op.drop_table("aion_capability_runtime_bindings")
    for column in (
        "created_at",
        "health_status",
        "status",
        "runtime_type",
        "version",
        "module_id",
    ):
        op.drop_index(f"ix_aion_module_runtimes_{column}", table_name="aion_module_runtimes")
    op.drop_table("aion_module_runtimes")
