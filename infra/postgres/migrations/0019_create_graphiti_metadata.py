"""Create Graphiti adapter metadata tables.

Revision ID: 0019_create_graphiti_metadata
Revises: 0018_create_turbovec_indexes
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019_create_graphiti_metadata"
down_revision = "0018_create_turbovec_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Graphiti config and sync metadata tables."""
    op.create_table(
        "aion_graphiti_configs",
        sa.Column("graphiti_config_id", sa.Text(), primary_key=True),
        sa.Column("config_name", sa.Text(), nullable=False),
        sa.Column("adapter_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("backend_type", sa.Text(), nullable=False),
        sa.Column("endpoint_ref", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("config_name", "adapter_name", "status", "backend_type", "created_at"):
        op.create_index(f"ix_aion_graphiti_configs_{column}", "aion_graphiti_configs", [column])

    op.create_table(
        "aion_graphiti_sync_records",
        sa.Column("sync_id", sa.Text(), primary_key=True),
        sa.Column(
            "graphiti_config_id",
            sa.Text(),
            sa.ForeignKey("aion_graphiti_configs.graphiti_config_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "graphiti_config_id",
        "source_type",
        "source_id",
        "target_type",
        "target_id",
        "status",
        "deleted_at",
        "created_at",
    ):
        op.create_index(
            f"ix_aion_graphiti_sync_records_{column}",
            "aion_graphiti_sync_records",
            [column],
        )


def downgrade() -> None:
    """Drop Graphiti metadata tables."""
    op.drop_table("aion_graphiti_sync_records")
    op.drop_table("aion_graphiti_configs")
