"""Create AION temporal graph memory tables.

Revision ID: 0005_create_aion_temporal_graph
Revises: 0004_create_aion_semantic_embeddings
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_create_aion_temporal_graph"
down_revision: str | None = "0004_create_aion_semantic_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create temporal graph memory tables."""
    op.create_table(
        "aion_graph_nodes",
        sa.Column("node_id", sa.Text(), primary_key=True),
        sa.Column("node_type", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_event_id", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Double(), nullable=False),
        sa.Column("sensitivity", sa.Text(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_graph_nodes_node_type", "aion_graph_nodes", ["node_type"])
    op.create_index("ix_aion_graph_nodes_label", "aion_graph_nodes", ["label"])
    op.create_index("ix_aion_graph_nodes_observed_at", "aion_graph_nodes", ["observed_at"])
    op.create_index("ix_aion_graph_nodes_source_event_id", "aion_graph_nodes", ["source_event_id"])
    op.create_index("ix_aion_graph_nodes_deleted_at", "aion_graph_nodes", ["deleted_at"])

    op.create_table(
        "aion_graph_edges",
        sa.Column("edge_id", sa.Text(), primary_key=True),
        sa.Column("edge_type", sa.Text(), nullable=False),
        sa.Column("from_node_id", sa.Text(), sa.ForeignKey("aion_graph_nodes.node_id"), nullable=False),
        sa.Column("to_node_id", sa.Text(), sa.ForeignKey("aion_graph_nodes.node_id"), nullable=False),
        sa.Column("owner_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_event_id", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Double(), nullable=False),
        sa.Column("sensitivity", sa.Text(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_graph_edges_edge_type", "aion_graph_edges", ["edge_type"])
    op.create_index("ix_aion_graph_edges_from_node_id", "aion_graph_edges", ["from_node_id"])
    op.create_index("ix_aion_graph_edges_to_node_id", "aion_graph_edges", ["to_node_id"])
    op.create_index("ix_aion_graph_edges_observed_at", "aion_graph_edges", ["observed_at"])
    op.create_index("ix_aion_graph_edges_source_event_id", "aion_graph_edges", ["source_event_id"])
    op.create_index("ix_aion_graph_edges_deleted_at", "aion_graph_edges", ["deleted_at"])


def downgrade() -> None:
    """Drop temporal graph memory tables."""
    op.drop_index("ix_aion_graph_edges_deleted_at", table_name="aion_graph_edges")
    op.drop_index("ix_aion_graph_edges_source_event_id", table_name="aion_graph_edges")
    op.drop_index("ix_aion_graph_edges_observed_at", table_name="aion_graph_edges")
    op.drop_index("ix_aion_graph_edges_to_node_id", table_name="aion_graph_edges")
    op.drop_index("ix_aion_graph_edges_from_node_id", table_name="aion_graph_edges")
    op.drop_index("ix_aion_graph_edges_edge_type", table_name="aion_graph_edges")
    op.drop_table("aion_graph_edges")

    op.drop_index("ix_aion_graph_nodes_deleted_at", table_name="aion_graph_nodes")
    op.drop_index("ix_aion_graph_nodes_source_event_id", table_name="aion_graph_nodes")
    op.drop_index("ix_aion_graph_nodes_observed_at", table_name="aion_graph_nodes")
    op.drop_index("ix_aion_graph_nodes_label", table_name="aion_graph_nodes")
    op.drop_index("ix_aion_graph_nodes_node_type", table_name="aion_graph_nodes")
    op.drop_table("aion_graph_nodes")
