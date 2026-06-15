"""Create MCP adapter metadata tables.

Revision ID: 0020_create_mcp_adapter_metadata
Revises: 0019_create_graphiti_metadata
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_create_mcp_adapter_metadata"
down_revision: str | None = "0019_create_graphiti_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create MCP tables."""
    op.create_table(
        "aion_mcp_servers",
        sa.Column("mcp_server_id", sa.Text(), primary_key=True),
        sa.Column("server_name", sa.Text(), nullable=False),
        sa.Column("transport_type", sa.Text(), nullable=False),
        sa.Column("endpoint_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("health_status", sa.Text(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_mcp_servers_server_name", "aion_mcp_servers", ["server_name"])
    op.create_index("ix_aion_mcp_servers_transport_type", "aion_mcp_servers", ["transport_type"])
    op.create_index("ix_aion_mcp_servers_status", "aion_mcp_servers", ["status"])
    op.create_index("ix_aion_mcp_servers_health_status", "aion_mcp_servers", ["health_status"])
    op.create_index("ix_aion_mcp_servers_created_at", "aion_mcp_servers", ["created_at"])

    op.create_table(
        "aion_mcp_capability_mappings",
        sa.Column("mapping_id", sa.Text(), primary_key=True),
        sa.Column("mcp_server_id", sa.Text(), sa.ForeignKey("aion_mcp_servers.mcp_server_id"), nullable=False),
        sa.Column("mcp_tool_name", sa.Text(), nullable=False),
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("permissions_required", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("memory_read_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("memory_write_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("mcp_server_id", "mcp_tool_name", name="uq_mcp_server_tool"),
        sa.UniqueConstraint("capability_id", name="uq_mcp_capability_id"),
    )
    op.create_index("ix_aion_mcp_mappings_server", "aion_mcp_capability_mappings", ["mcp_server_id"])
    op.create_index("ix_aion_mcp_mappings_tool", "aion_mcp_capability_mappings", ["mcp_tool_name"])
    op.create_index("ix_aion_mcp_mappings_capability", "aion_mcp_capability_mappings", ["capability_id"])
    op.create_index("ix_aion_mcp_mappings_module", "aion_mcp_capability_mappings", ["module_id"])
    op.create_index("ix_aion_mcp_mappings_risk", "aion_mcp_capability_mappings", ["risk_level"])
    op.create_index("ix_aion_mcp_mappings_status", "aion_mcp_capability_mappings", ["status"])
    op.create_index("ix_aion_mcp_mappings_created_at", "aion_mcp_capability_mappings", ["created_at"])

    op.create_table(
        "aion_mcp_sync_records",
        sa.Column("sync_id", sa.Text(), primary_key=True),
        sa.Column("mcp_server_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("discovered_tools", sa.Integer(), nullable=False),
        sa.Column("mapped_capabilities", sa.Integer(), nullable=False),
        sa.Column("skipped", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
        sa.Column("errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aion_mcp_sync_server", "aion_mcp_sync_records", ["mcp_server_id"])
    op.create_index("ix_aion_mcp_sync_status", "aion_mcp_sync_records", ["status"])
    op.create_index("ix_aion_mcp_sync_created_at", "aion_mcp_sync_records", ["created_at"])

    op.create_table(
        "aion_mcp_invocation_records",
        sa.Column("mcp_invocation_id", sa.Text(), primary_key=True),
        sa.Column("invocation_id", sa.Text(), nullable=True),
        sa.Column("mcp_server_id", sa.Text(), nullable=False),
        sa.Column("mcp_tool_name", sa.Text(), nullable=False),
        sa.Column("capability_id", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("step_run_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("request", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("policy_decision_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aion_mcp_invocation_invocation", "aion_mcp_invocation_records", ["invocation_id"])
    op.create_index("ix_aion_mcp_invocation_server", "aion_mcp_invocation_records", ["mcp_server_id"])
    op.create_index("ix_aion_mcp_invocation_tool", "aion_mcp_invocation_records", ["mcp_tool_name"])
    op.create_index("ix_aion_mcp_invocation_capability", "aion_mcp_invocation_records", ["capability_id"])
    op.create_index("ix_aion_mcp_invocation_trace", "aion_mcp_invocation_records", ["trace_id"])
    op.create_index("ix_aion_mcp_invocation_execution", "aion_mcp_invocation_records", ["execution_id"])
    op.create_index("ix_aion_mcp_invocation_status", "aion_mcp_invocation_records", ["status"])
    op.create_index("ix_aion_mcp_invocation_created_at", "aion_mcp_invocation_records", ["created_at"])


def downgrade() -> None:
    """Drop MCP tables."""
    op.drop_table("aion_mcp_invocation_records")
    op.drop_table("aion_mcp_sync_records")
    op.drop_table("aion_mcp_capability_mappings")
    op.drop_table("aion_mcp_servers")
