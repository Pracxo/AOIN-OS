"""Create Evidence Vault tables.

Revision ID: 0013_create_evidence_vault
Revises: 0012_create_identity_scope_control_plane
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_create_evidence_vault"
down_revision = "0012_create_identity_scope_control_plane"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create evidence tables."""
    op.create_table(
        "aion_evidence_records",
        sa.Column("evidence_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("owner_scope", _jsonb(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("content_ref", sa.Text(), nullable=True),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("sensitivity", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_evidence_records_trace_id", "aion_evidence_records", ["trace_id"])
    op.create_index(
        "ix_aion_evidence_records_source_type",
        "aion_evidence_records",
        ["source_type"],
    )
    op.create_index(
        "ix_aion_evidence_records_content_hash",
        "aion_evidence_records",
        ["content_hash"],
    )
    op.create_index(
        "ix_aion_evidence_records_sensitivity",
        "aion_evidence_records",
        ["sensitivity"],
    )
    op.create_index(
        "ix_aion_evidence_records_created_at",
        "aion_evidence_records",
        ["created_at"],
    )
    op.create_index(
        "ix_aion_evidence_records_deleted_at",
        "aion_evidence_records",
        ["deleted_at"],
    )

    op.create_table(
        "aion_evidence_chunks",
        sa.Column("chunk_id", sa.Text(), primary_key=True),
        sa.Column(
            "evidence_id",
            sa.Text(),
            sa.ForeignKey("aion_evidence_records.evidence_id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.Text(), nullable=False),
        sa.Column("token_count_hint", sa.Integer(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_evidence_chunks_evidence_id", "aion_evidence_chunks", ["evidence_id"])
    op.create_index("ix_aion_evidence_chunks_chunk_index", "aion_evidence_chunks", ["chunk_index"])
    op.create_index("ix_aion_evidence_chunks_text_hash", "aion_evidence_chunks", ["text_hash"])
    op.create_index("ix_aion_evidence_chunks_deleted_at", "aion_evidence_chunks", ["deleted_at"])

    op.create_table(
        "aion_evidence_links",
        sa.Column("link_id", sa.Text(), primary_key=True),
        sa.Column(
            "evidence_id",
            sa.Text(),
            sa.ForeignKey("aion_evidence_records.evidence_id"),
            nullable=False,
        ),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("relation_type", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", _jsonb(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_evidence_links_evidence_id", "aion_evidence_links", ["evidence_id"])
    op.create_index("ix_aion_evidence_links_target_type", "aion_evidence_links", ["target_type"])
    op.create_index("ix_aion_evidence_links_target_id", "aion_evidence_links", ["target_id"])
    op.create_index(
        "ix_aion_evidence_links_relation_type",
        "aion_evidence_links",
        ["relation_type"],
    )
    op.create_index("ix_aion_evidence_links_trace_id", "aion_evidence_links", ["trace_id"])
    op.create_index("ix_aion_evidence_links_deleted_at", "aion_evidence_links", ["deleted_at"])

    op.create_table(
        "aion_grounding_claims",
        sa.Column("claim_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("evidence_refs", _jsonb(), nullable=False),
        sa.Column("chunk_refs", _jsonb(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aion_grounding_claims_trace_id", "aion_grounding_claims", ["trace_id"])
    op.create_index(
        "ix_aion_grounding_claims_verification_status",
        "aion_grounding_claims",
        ["verification_status"],
    )
    op.create_index("ix_aion_grounding_claims_score", "aion_grounding_claims", ["score"])
    op.create_index(
        "ix_aion_grounding_claims_created_at",
        "aion_grounding_claims",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop evidence tables."""
    op.drop_table("aion_grounding_claims")
    op.drop_table("aion_evidence_links")
    op.drop_table("aion_evidence_chunks")
    op.drop_table("aion_evidence_records")
