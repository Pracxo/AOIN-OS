"""Create AION semantic embeddings table.

Revision ID: 0004_create_aion_semantic_embeddings
Revises: 0003_create_aion_audit_learning_telemetry
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_create_aion_semantic_embeddings"
down_revision: str | None = "0003_create_aion_audit_learning_telemetry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create pgvector extension and semantic embedding table."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS aion_semantic_embeddings (
            embedding_id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            adapter_name TEXT NOT NULL,
            embedding_model TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            embedding VECTOR(384) NOT NULL,
            source_text_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ NULL
        )
        """
    )
    op.create_index("ix_aion_semantic_embeddings_memory_id", "aion_semantic_embeddings", ["memory_id"])
    op.create_index(
        "ix_aion_semantic_embeddings_adapter_name",
        "aion_semantic_embeddings",
        ["adapter_name"],
    )
    op.create_index(
        "ix_aion_semantic_embeddings_dimensions",
        "aion_semantic_embeddings",
        ["dimensions"],
    )
    op.create_index(
        "ix_aion_semantic_embeddings_deleted_at",
        "aion_semantic_embeddings",
        ["deleted_at"],
    )
    try:
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_aion_semantic_embeddings_embedding_cosine
            ON aion_semantic_embeddings USING ivfflat
            (embedding vector_cosine_ops) WITH (lists = 100)
            """
        )
    except Exception:
        pass


def downgrade() -> None:
    """Drop semantic embedding table."""
    op.drop_index(
        "ix_aion_semantic_embeddings_embedding_cosine",
        table_name="aion_semantic_embeddings",
        if_exists=True,
    )
    op.drop_index("ix_aion_semantic_embeddings_deleted_at", table_name="aion_semantic_embeddings")
    op.drop_index("ix_aion_semantic_embeddings_dimensions", table_name="aion_semantic_embeddings")
    op.drop_index("ix_aion_semantic_embeddings_adapter_name", table_name="aion_semantic_embeddings")
    op.drop_index("ix_aion_semantic_embeddings_memory_id", table_name="aion_semantic_embeddings")
    op.drop_table("aion_semantic_embeddings")
