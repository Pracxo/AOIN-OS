"""Safe API request audit persistence."""

from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.api import AIONError, APIRequestRecord, RequestContext

api_request_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_api_request_records = Table(
    "aion_api_request_records",
    api_request_metadata,
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
    Column("request_metadata", json_payload_type, nullable=False),
    Column("response_metadata", json_payload_type, nullable=False),
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


class APIRequestAuditService:
    """Persist safe request audit records without bodies or raw headers."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            self._engine = _create_engine(database_url)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def start_record(self, context: RequestContext, request: Request) -> APIRequestRecord:
        """Create an initial audit record for one request."""
        self._ensure_schema()
        record = APIRequestRecord(
            request_id=context.request_id,
            trace_id=context.trace_id,
            correlation_id=context.correlation_id,
            idempotency_key=context.idempotency_key,
            actor_id=context.actor_id,
            workspace_id=context.workspace_id,
            method=context.method,
            path=context.path,
            route_name=context.route_name,
            status_code=None,
            duration_ms=None,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_code=None,
            error_category=None,
            request_metadata={"query_param_count": len(request.query_params)},
            response_metadata={},
            created_at=context.started_at,
            completed_at=None,
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_api_request_records).values(**record.model_dump(mode="python"))
            )
        return record

    def complete_record(
        self,
        request_id: str,
        status_code: int,
        response_metadata: dict[str, Any],
        error: AIONError | None = None,
    ) -> APIRequestRecord:
        """Complete one audit record with status and sanitized error metadata."""
        self._ensure_schema()
        completed_at = datetime.now(UTC)
        existing = self.get_record(request_id)
        if existing is None:
            raise KeyError(request_id)
        duration_ms = (
            int((completed_at - existing.created_at).total_seconds() * 1000)
            if existing.created_at
            else None
        )
        values = {
            "status_code": status_code,
            "duration_ms": duration_ms,
            "response_metadata": response_metadata,
            "error_code": error.code if error else None,
            "error_category": error.category if error else None,
            "completed_at": completed_at,
        }
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_api_request_records)
                .where(aion_api_request_records.c.request_id == request_id)
                .values(**values)
            )
        stored = self.get_record(request_id)
        if stored is None:
            raise KeyError(request_id)
        return stored

    def get_record(self, request_id: str) -> APIRequestRecord | None:
        """Return one audit record by request ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_api_request_records).where(
                        aion_api_request_records.c.request_id == request_id
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_record(row)

    def list_records(
        self,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        limit: int = 50,
    ) -> list[APIRequestRecord]:
        """Return recent safe request audit records."""
        self._ensure_schema()
        statement = (
            select(aion_api_request_records)
            .order_by(aion_api_request_records.c.created_at.desc())
            .limit(limit)
        )
        if trace_id is not None:
            statement = statement.where(aion_api_request_records.c.trace_id == trace_id)
        if correlation_id is not None:
            statement = statement.where(
                aion_api_request_records.c.correlation_id == correlation_id
            )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_record(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        api_request_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_record(row: RowMapping) -> APIRequestRecord:
    return APIRequestRecord(
        request_id=str(row["request_id"]),
        trace_id=_optional_str(row["trace_id"]),
        correlation_id=_optional_str(row["correlation_id"]),
        idempotency_key=_optional_str(row["idempotency_key"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        method=str(row["method"]),
        path=str(row["path"]),
        route_name=_optional_str(row["route_name"]),
        status_code=_optional_int(row["status_code"]),
        duration_ms=_optional_int(row["duration_ms"]),
        client_host=_optional_str(row["client_host"]),
        user_agent=_optional_str(row["user_agent"]),
        error_code=_optional_str(row["error_code"]),
        error_category=_optional_str(row["error_category"]),
        request_metadata=_dict(row["request_metadata"]),
        response_metadata=_dict(row["response_metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    raise TypeError("Expected datetime-compatible value")
