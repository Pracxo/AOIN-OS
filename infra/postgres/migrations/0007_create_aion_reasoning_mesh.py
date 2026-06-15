"""Create AION reasoning mesh and model call ledger tables.

Revision ID: 0007_create_aion_reasoning_mesh
Revises: 0006_create_aion_context_retrievals
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_create_aion_reasoning_mesh"
down_revision: str | None = "0006_create_aion_context_retrievals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create reasoning and model call ledger tables."""
    op.add_column(
        "aion_decision_traces",
        sa.Column(
            "reasoning_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column("aion_decision_traces", "reasoning_refs", server_default=None)

    op.create_table(
        "aion_reasoning_runs",
        sa.Column("reasoning_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("intent_id", sa.Text(), nullable=True),
        sa.Column("context_id", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("prompt_packet", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("route_decision", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_aion_reasoning_runs_trace_id", "aion_reasoning_runs", ["trace_id"])
    op.create_index("ix_aion_reasoning_runs_intent_id", "aion_reasoning_runs", ["intent_id"])
    op.create_index("ix_aion_reasoning_runs_context_id", "aion_reasoning_runs", ["context_id"])
    op.create_index("ix_aion_reasoning_runs_mode", "aion_reasoning_runs", ["mode"])
    op.create_index("ix_aion_reasoning_runs_status", "aion_reasoning_runs", ["status"])
    op.create_index("ix_aion_reasoning_runs_created_at", "aion_reasoning_runs", ["created_at"])

    op.create_table(
        "aion_model_call_records",
        sa.Column("model_call_id", sa.Text(), primary_key=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("reasoning_id", sa.Text(), nullable=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("request", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_estimate", sa.Double(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_aion_model_call_records_trace_id", "aion_model_call_records", ["trace_id"])
    op.create_index(
        "ix_aion_model_call_records_reasoning_id",
        "aion_model_call_records",
        ["reasoning_id"],
    )
    op.create_index("ix_aion_model_call_records_provider", "aion_model_call_records", ["provider"])
    op.create_index("ix_aion_model_call_records_model", "aion_model_call_records", ["model"])
    op.create_index("ix_aion_model_call_records_mode", "aion_model_call_records", ["mode"])
    op.create_index("ix_aion_model_call_records_status", "aion_model_call_records", ["status"])
    op.create_index("ix_aion_model_call_records_created_at", "aion_model_call_records", ["created_at"])


def downgrade() -> None:
    """Drop reasoning and model call ledger tables."""
    op.drop_index("ix_aion_model_call_records_created_at", table_name="aion_model_call_records")
    op.drop_index("ix_aion_model_call_records_status", table_name="aion_model_call_records")
    op.drop_index("ix_aion_model_call_records_mode", table_name="aion_model_call_records")
    op.drop_index("ix_aion_model_call_records_model", table_name="aion_model_call_records")
    op.drop_index("ix_aion_model_call_records_provider", table_name="aion_model_call_records")
    op.drop_index(
        "ix_aion_model_call_records_reasoning_id",
        table_name="aion_model_call_records",
    )
    op.drop_index("ix_aion_model_call_records_trace_id", table_name="aion_model_call_records")
    op.drop_table("aion_model_call_records")

    op.drop_index("ix_aion_reasoning_runs_created_at", table_name="aion_reasoning_runs")
    op.drop_index("ix_aion_reasoning_runs_status", table_name="aion_reasoning_runs")
    op.drop_index("ix_aion_reasoning_runs_mode", table_name="aion_reasoning_runs")
    op.drop_index("ix_aion_reasoning_runs_context_id", table_name="aion_reasoning_runs")
    op.drop_index("ix_aion_reasoning_runs_intent_id", table_name="aion_reasoning_runs")
    op.drop_index("ix_aion_reasoning_runs_trace_id", table_name="aion_reasoning_runs")
    op.drop_table("aion_reasoning_runs")
    op.drop_column("aion_decision_traces", "reasoning_refs")
