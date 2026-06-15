"""Create identity and scope control plane tables.

Revision ID: 0012_create_identity_scope_control_plane
Revises: 0011_create_reflection_skill_registry
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0012_create_identity_scope_control_plane"
down_revision: str | None = "0011_create_reflection_skill_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create identity and scope control plane tables."""
    op.create_table(
        "aion_actors",
        sa.Column("actor_id", sa.Text(), primary_key=True),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("actor_type", "status", "created_at"):
        op.create_index(f"ix_aion_actors_{column}", "aion_actors", [column])

    op.create_table(
        "aion_workspaces",
        sa.Column("workspace_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_actor_id", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("name", "status", "owner_actor_id", "created_at"):
        op.create_index(f"ix_aion_workspaces_{column}", "aion_workspaces", [column])

    op.create_table(
        "aion_workspace_memberships",
        sa.Column("membership_id", sa.Text(), primary_key=True),
        sa.Column("workspace_id", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("granted_by", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("workspace_id", "actor_id", name="uq_aion_workspace_actor"),
    )
    for column in ("workspace_id", "actor_id", "role", "status", "created_at"):
        op.create_index(
            f"ix_aion_workspace_memberships_{column}",
            "aion_workspace_memberships",
            [column],
        )

    op.create_table(
        "aion_permission_grants",
        sa.Column("grant_id", sa.Text(), primary_key=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("permission", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("effect", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("granted_by", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in (
        "actor_id",
        "workspace_id",
        "role",
        "permission",
        "resource_type",
        "resource_id",
        "effect",
        "status",
        "expires_at",
        "created_at",
    ):
        op.create_index(f"ix_aion_permission_grants_{column}", "aion_permission_grants", [column])

    op.create_table(
        "aion_scope_resolution_records",
        sa.Column("scope_resolution_id", sa.Text(), primary_key=True),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("workspace_id", sa.Text(), nullable=True),
        sa.Column("requested_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resolved_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("decision", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    for column in ("actor_id", "workspace_id", "created_at"):
        op.create_index(
            f"ix_aion_scope_resolution_records_{column}",
            "aion_scope_resolution_records",
            [column],
        )


def downgrade() -> None:
    """Drop identity and scope control plane tables."""
    op.drop_table("aion_scope_resolution_records")
    op.drop_table("aion_permission_grants")
    op.drop_table("aion_workspace_memberships")
    op.drop_table("aion_workspaces")
    op.drop_table("aion_actors")
