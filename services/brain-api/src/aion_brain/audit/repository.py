"""Persistent audit repository for traces, decisions, learning, and telemetry."""

import json
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    inspect,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal, LearningType
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.contracts.traces import DecisionTrace

audit_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_decision_traces = Table(
    "aion_decision_traces",
    audit_metadata,
    Column("trace_id", Text, primary_key=True),
    Column("event_id", Text, nullable=False),
    Column("intent_id", Text, nullable=True),
    Column("context_id", Text, nullable=True),
    Column("plan_id", Text, nullable=True),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("capability_refs", json_payload_type, nullable=False),
    Column("reasoning_refs", json_payload_type, nullable=False),
    Column("execution_refs", json_payload_type, nullable=False),
    Column("policy_decisions", json_payload_type, nullable=False),
    Column("outcome", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_decision_traces_event_id", "event_id"),
    Index("ix_aion_decision_traces_created_at", "created_at"),
)

aion_policy_decisions = Table(
    "aion_policy_decisions",
    audit_metadata,
    Column("decision_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=False),
    Column("decision", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_policy_decisions_trace_id", "trace_id"),
)

aion_learning_signals = Table(
    "aion_learning_signals",
    audit_metadata,
    Column("learning_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=False),
    Column("learning_type", Text, nullable=False),
    Column("signal", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("promotion_status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_learning_signals_trace_id", "trace_id"),
)

aion_evaluations = Table(
    "aion_evaluations",
    audit_metadata,
    Column("evaluation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=False),
    Column("scores", json_payload_type, nullable=False),
    Column("lessons", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_evaluations_trace_id", "trace_id"),
)

aion_visual_telemetry = Table(
    "aion_visual_telemetry",
    audit_metadata,
    Column("telemetry_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=False),
    Column("event_type", Text, nullable=False),
    Column("node_type", Text, nullable=False),
    Column("node_id", Text, nullable=False),
    Column("edge_from", Text, nullable=True),
    Column("edge_to", Text, nullable=True),
    Column("intensity", Float, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_visual_telemetry_trace_id", "trace_id"),
    Index("ix_aion_visual_telemetry_event_type", "event_type"),
)


class AuditRepository:
    """Repository for persisted Brain trace artifacts."""

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

    def save_trace(self, trace: DecisionTrace) -> DecisionTrace:
        """Persist a decision trace."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_decision_traces).where(
                    aion_decision_traces.c.trace_id == trace.trace_id
                )
            )
            connection.execute(
                insert(aion_decision_traces).values(**trace.model_dump(mode="python"))
            )
        return trace

    def get_trace(self, trace_id: str) -> DecisionTrace | None:
        """Return a decision trace."""
        self._ensure_schema()
        statement = select(aion_decision_traces).where(aion_decision_traces.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_trace(row)

    def save_policy_decisions(
        self,
        trace_id: str,
        decisions: list[PolicyDecision],
    ) -> list[PolicyDecision]:
        """Persist policy decisions for a trace."""
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_policy_decisions).where(aion_policy_decisions.c.trace_id == trace_id)
            )
            for decision in decisions:
                connection.execute(
                    insert(aion_policy_decisions).values(
                        decision_id=decision.decision_id,
                        trace_id=trace_id,
                        decision=decision.model_dump(mode="json"),
                        created_at=now,
                    )
                )
        return decisions

    def list_policy_decisions(self, trace_id: str) -> list[PolicyDecision]:
        """Return persisted policy decisions for a trace."""
        self._ensure_schema()
        statement = (
            select(aion_policy_decisions)
            .where(aion_policy_decisions.c.trace_id == trace_id)
            .order_by(aion_policy_decisions.c.created_at)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [PolicyDecision.model_validate(row["decision"]) for row in rows]

    def save_evaluation(self, evaluation: EvaluationRecord) -> EvaluationRecord:
        """Persist an evaluation record."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_evaluations).where(aion_evaluations.c.trace_id == evaluation.trace_id)
            )
            connection.execute(insert(aion_evaluations).values(**evaluation.model_dump(mode="python")))
        return evaluation

    def get_evaluation(self, trace_id: str) -> EvaluationRecord | None:
        """Return an evaluation by trace ID."""
        self._ensure_schema()
        statement = select(aion_evaluations).where(aion_evaluations.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_evaluation(row)

    def save_learning_signal(self, signal: LearningSignal) -> LearningSignal:
        """Persist a learning signal candidate."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_learning_signals).where(
                    aion_learning_signals.c.learning_id == signal.learning_id
                )
            )
            connection.execute(insert(aion_learning_signals).values(**signal.model_dump(mode="python")))
        return signal

    def list_learning_signals(self, trace_id: str) -> list[LearningSignal]:
        """Return learning signals by trace ID."""
        self._ensure_schema()
        statement = (
            select(aion_learning_signals)
            .where(aion_learning_signals.c.trace_id == trace_id)
            .order_by(aion_learning_signals.c.created_at)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_learning_signal(row) for row in rows]

    def save_visual_telemetry(
        self,
        trace_id: str,
        events: list[VisualTelemetryEvent],
    ) -> list[VisualTelemetryEvent]:
        """Persist visual telemetry events for a trace."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_visual_telemetry).where(aion_visual_telemetry.c.trace_id == trace_id)
            )
            for event in events:
                connection.execute(
                    insert(aion_visual_telemetry).values(**event.model_dump(mode="python"))
                )
        return events

    def list_visual_telemetry(self, trace_id: str) -> list[VisualTelemetryEvent]:
        """Return visual telemetry by trace ID."""
        self._ensure_schema()
        statement = (
            select(aion_visual_telemetry)
            .where(aion_visual_telemetry.c.trace_id == trace_id)
            .order_by(aion_visual_telemetry.c.created_at)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_visual_telemetry(row) for row in rows]

    def emit(self, event: VisualTelemetryEvent) -> None:
        """Append one visual telemetry event without replacing trace history."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_visual_telemetry).where(
                    aion_visual_telemetry.c.telemetry_id == event.telemetry_id
                )
            )
            connection.execute(
                insert(aion_visual_telemetry).values(**event.model_dump(mode="python"))
            )

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        audit_metadata.create_all(self._engine)
        self._ensure_trace_reasoning_refs_column()
        self._ensure_trace_execution_refs_column()
        self._schema_ready = True

    def _ensure_trace_reasoning_refs_column(self) -> None:
        inspector = inspect(self._engine)
        if "aion_decision_traces" not in inspector.get_table_names():
            return
        column_names = {
            str(column["name"]) for column in inspector.get_columns("aion_decision_traces")
        }
        if "reasoning_refs" in column_names:
            return
        statement = (
            "ALTER TABLE aion_decision_traces "
            "ADD COLUMN reasoning_refs JSONB NOT NULL DEFAULT '[]'::jsonb"
            if self._engine.dialect.name == "postgresql"
            else "ALTER TABLE aion_decision_traces "
            "ADD COLUMN reasoning_refs JSON NOT NULL DEFAULT '[]'"
        )
        with self._engine.begin() as connection:
            connection.execute(text(statement))

    def _ensure_trace_execution_refs_column(self) -> None:
        inspector = inspect(self._engine)
        if "aion_decision_traces" not in inspector.get_table_names():
            return
        column_names = {
            str(column["name"]) for column in inspector.get_columns("aion_decision_traces")
        }
        if "execution_refs" in column_names:
            return
        statement = (
            "ALTER TABLE aion_decision_traces "
            "ADD COLUMN execution_refs JSONB NOT NULL DEFAULT '[]'::jsonb"
            if self._engine.dialect.name == "postgresql"
            else "ALTER TABLE aion_decision_traces "
            "ADD COLUMN execution_refs JSON NOT NULL DEFAULT '[]'"
        )
        with self._engine.begin() as connection:
            connection.execute(text(statement))


def _row_to_trace(row: RowMapping) -> DecisionTrace:
    return DecisionTrace(
        trace_id=str(row["trace_id"]),
        event_id=str(row["event_id"]),
        intent_id=_optional_str(row["intent_id"]),
        context_id=_optional_str(row["context_id"]),
        plan_id=_optional_str(row["plan_id"]),
        memory_refs=_json_string_list(row["memory_refs"]),
        capability_refs=_json_string_list(row["capability_refs"]),
        reasoning_refs=_json_string_list(row["reasoning_refs"]),
        execution_refs=_json_string_list(row["execution_refs"]),
        policy_decisions=_json_string_list(row["policy_decisions"]),
        outcome=dict(row["outcome"]),
        created_at=_coerce_datetime(row["created_at"]),
    )


def _row_to_evaluation(row: RowMapping) -> EvaluationRecord:
    return EvaluationRecord(
        evaluation_id=str(row["evaluation_id"]),
        trace_id=str(row["trace_id"]),
        scores={str(key): float(value) for key, value in dict(row["scores"]).items()},
        lessons=[str(item) for item in list(row["lessons"])],
        created_at=_coerce_datetime(row["created_at"]),
    )


def _row_to_learning_signal(row: RowMapping) -> LearningSignal:
    return LearningSignal(
        learning_id=str(row["learning_id"]),
        trace_id=str(row["trace_id"]),
        learning_type=cast(LearningType, str(row["learning_type"])),
        signal=dict(row["signal"]),
        confidence=float(row["confidence"]),
        promotion_status="candidate",
        created_at=_coerce_datetime(row["created_at"]),
    )


def _row_to_visual_telemetry(row: RowMapping) -> VisualTelemetryEvent:
    return VisualTelemetryEvent(
        telemetry_id=str(row["telemetry_id"]),
        trace_id=str(row["trace_id"]),
        event_type=cast(VisualTelemetryEventType, str(row["event_type"])),
        node_type=cast(VisualNodeType, str(row["node_type"])),
        node_id=str(row["node_id"]),
        edge_from=_optional_str(row["edge_from"]),
        edge_to=_optional_str(row["edge_to"]),
        intensity=float(row["intensity"]),
        payload=dict(row["payload"]),
        created_at=_coerce_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _json_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(decoded, list):
            return [str(item) for item in decoded]
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
