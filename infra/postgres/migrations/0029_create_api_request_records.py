"""Create API request audit records table."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

aion_api_request_records = Table(
    "aion_api_request_records",
    metadata,
    Column("request_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("idempotency_key", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("method", Text, nullable=False),
    Column("path", Text, nullable=False),
    Column("route_name", Text, nullable=True),
    Column("status_code", Integer, nullable=True),
    Column("duration_ms", Integer, nullable=True),
    Column("client_host", Text, nullable=True),
    Column("user_agent", Text, nullable=True),
    Column("error_code", Text, nullable=True),
    Column("error_category", Text, nullable=True),
    Column("request_metadata", JSONB, nullable=False),
    Column("response_metadata", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_api_request_records_trace_id", "trace_id"),
    Index("ix_aion_api_request_records_correlation_id", "correlation_id"),
    Index("ix_aion_api_request_records_idempotency_key", "idempotency_key"),
    Index("ix_aion_api_request_records_actor_id", "actor_id"),
    Index("ix_aion_api_request_records_workspace_id", "workspace_id"),
    Index("ix_aion_api_request_records_method", "method"),
    Index("ix_aion_api_request_records_path", "path"),
    Index("ix_aion_api_request_records_status_code", "status_code"),
    Index("ix_aion_api_request_records_error_code", "error_code"),
    Index("ix_aion_api_request_records_error_category", "error_category"),
    Index("ix_aion_api_request_records_created_at", "created_at"),
)
