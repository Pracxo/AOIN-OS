"""Persistent reasoning and model call ledger repository."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.reasoning import ModelCallRecord, ReasoningResult

reasoning_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_reasoning_runs = Table(
    "aion_reasoning_runs",
    reasoning_metadata,
    Column("reasoning_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("intent_id", Text, nullable=True),
    Column("context_id", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("prompt_packet", json_payload_type, nullable=False),
    Column("route_decision", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_reasoning_runs_trace_id", "trace_id"),
    Index("ix_aion_reasoning_runs_intent_id", "intent_id"),
    Index("ix_aion_reasoning_runs_context_id", "context_id"),
    Index("ix_aion_reasoning_runs_mode", "mode"),
    Index("ix_aion_reasoning_runs_status", "status"),
    Index("ix_aion_reasoning_runs_created_at", "created_at"),
)

aion_model_call_records = Table(
    "aion_model_call_records",
    reasoning_metadata,
    Column("model_call_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("reasoning_id", Text, nullable=True),
    Column("provider", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("request", json_payload_type, nullable=False),
    Column("response", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("cost_estimate", Float, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_model_call_records_trace_id", "trace_id"),
    Index("ix_aion_model_call_records_reasoning_id", "reasoning_id"),
    Index("ix_aion_model_call_records_provider", "provider"),
    Index("ix_aion_model_call_records_model", "model"),
    Index("ix_aion_model_call_records_mode", "mode"),
    Index("ix_aion_model_call_records_status", "status"),
    Index("ix_aion_model_call_records_created_at", "created_at"),
)


class ReasoningRepository:
    """Repository for reasoning runs and model call ledger records."""

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
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_pre_ping=True,
            )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_reasoning(
        self,
        result: ReasoningResult,
        *,
        status: str = "completed",
    ) -> ReasoningResult:
        """Persist a reasoning run."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_reasoning_runs).where(
                    aion_reasoning_runs.c.reasoning_id == result.reasoning_id
                )
            )
            connection.execute(
                insert(aion_reasoning_runs).values(
                    reasoning_id=result.reasoning_id,
                    trace_id=result.trace_id,
                    intent_id=result.prompt_packet.intent_id,
                    context_id=result.context_id,
                    mode=result.mode,
                    prompt_packet=result.prompt_packet.model_dump(mode="json"),
                    route_decision=result.route_decision.model_dump(mode="json"),
                    result=result.model_dump(mode="json"),
                    status=status,
                    created_at=result.created_at,
                )
            )
        return result

    def get_reasoning(self, reasoning_id: str) -> ReasoningResult | None:
        """Return a persisted reasoning run."""
        self._ensure_schema()
        statement = select(aion_reasoning_runs).where(
            aion_reasoning_runs.c.reasoning_id == reasoning_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_reasoning(row)

    def save_model_call(self, record: ModelCallRecord) -> ModelCallRecord:
        """Persist a model call ledger record."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_model_call_records).where(
                    aion_model_call_records.c.model_call_id == record.model_call_id
                )
            )
            connection.execute(
                insert(aion_model_call_records).values(**record.model_dump(mode="python"))
            )
        return record

    def get_model_call(self, model_call_id: str) -> ModelCallRecord | None:
        """Return a persisted model call record."""
        self._ensure_schema()
        statement = select(aion_model_call_records).where(
            aion_model_call_records.c.model_call_id == model_call_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_model_call(row)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        reasoning_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_reasoning(row: RowMapping) -> ReasoningResult:
    return ReasoningResult.model_validate(dict(row["result"]))


def _row_to_model_call(row: RowMapping) -> ModelCallRecord:
    return ModelCallRecord(
        model_call_id=str(row["model_call_id"]),
        trace_id=_optional_str(row["trace_id"]),
        reasoning_id=_optional_str(row["reasoning_id"]),
        provider=str(row["provider"]),
        model=str(row["model"]),
        mode=row["mode"],
        request=dict(row["request"]),
        response=dict(row["response"]),
        status=str(row["status"]),
        latency_ms=_optional_int(row["latency_ms"]),
        cost_estimate=_optional_float(row["cost_estimate"]),
        created_at=_coerce_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
