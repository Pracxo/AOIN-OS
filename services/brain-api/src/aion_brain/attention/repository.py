"""Attention control persistence."""

from datetime import UTC, datetime
from typing import Any, cast

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
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.attention import (
    AttentionDecision,
    AttentionDecisionType,
    AttentionSignal,
    AttentionSignalType,
    ContextBudget,
    FocusSession,
    FocusStatus,
    FocusType,
    InterruptRecord,
    InterruptStatus,
    InterruptType,
)

attention_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_focus_sessions = Table(
    "aion_focus_sessions",
    attention_metadata,
    Column("focus_session_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("focus_type", Text, nullable=False),
    Column("active_goal_id", Text, nullable=True),
    Column("active_task_id", Text, nullable=True),
    Column("active_workflow_run_id", Text, nullable=True),
    Column("active_trace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("paused_at", DateTime(timezone=True), nullable=True),
    Column("ended_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_focus_sessions_trace_id", "trace_id"),
    Index("ix_aion_focus_sessions_actor_id", "actor_id"),
    Index("ix_aion_focus_sessions_workspace_id", "workspace_id"),
    Index("ix_aion_focus_sessions_status", "status"),
    Index("ix_aion_focus_sessions_focus_type", "focus_type"),
    Index("ix_aion_focus_sessions_active_goal_id", "active_goal_id"),
    Index("ix_aion_focus_sessions_active_task_id", "active_task_id"),
    Index("ix_aion_focus_sessions_active_workflow_run_id", "active_workflow_run_id"),
    Index("ix_aion_focus_sessions_created_at", "created_at"),
)

aion_attention_signals = Table(
    "aion_attention_signals",
    attention_metadata,
    Column("attention_signal_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("signal_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("title", Text, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("urgency", Float, nullable=False),
    Column("importance", Float, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("handled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_attention_signals_trace_id", "trace_id"),
    Index("ix_aion_attention_signals_actor_id", "actor_id"),
    Index("ix_aion_attention_signals_workspace_id", "workspace_id"),
    Index("ix_aion_attention_signals_signal_type", "signal_type"),
    Index("ix_aion_attention_signals_source_type", "source_type"),
    Index("ix_aion_attention_signals_source_id", "source_id"),
    Index("ix_aion_attention_signals_urgency", "urgency"),
    Index("ix_aion_attention_signals_importance", "importance"),
    Index("ix_aion_attention_signals_risk_level", "risk_level"),
    Index("ix_aion_attention_signals_handled_at", "handled_at"),
    Index("ix_aion_attention_signals_created_at", "created_at"),
)

aion_attention_decisions = Table(
    "aion_attention_decisions",
    attention_metadata,
    Column("attention_decision_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("focus_session_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("decision_type", Text, nullable=False),
    Column("selected_signal_ids", json_payload_type, nullable=False),
    Column("selected_slot_ids", json_payload_type, nullable=False),
    Column("selected_memory_ids", json_payload_type, nullable=False),
    Column("selected_evidence_ids", json_payload_type, nullable=False),
    Column("selected_skill_ids", json_payload_type, nullable=False),
    Column("selected_capability_ids", json_payload_type, nullable=False),
    Column("priority_score", Float, nullable=False),
    Column("reason", Text, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_attention_decisions_trace_id", "trace_id"),
    Index("ix_aion_attention_decisions_focus_session_id", "focus_session_id"),
    Index("ix_aion_attention_decisions_actor_id", "actor_id"),
    Index("ix_aion_attention_decisions_workspace_id", "workspace_id"),
    Index("ix_aion_attention_decisions_decision_type", "decision_type"),
    Index("ix_aion_attention_decisions_priority_score", "priority_score"),
    Index("ix_aion_attention_decisions_created_at", "created_at"),
)

aion_context_budgets = Table(
    "aion_context_budgets",
    attention_metadata,
    Column("context_budget_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("focus_session_id", Text, nullable=True),
    Column("intent_id", Text, nullable=True),
    Column("context_id", Text, nullable=True),
    Column("max_items", Integer, nullable=False),
    Column("max_chars", Integer, nullable=False),
    Column("allocation", json_payload_type, nullable=False),
    Column("used_items", Integer, nullable=False),
    Column("used_chars", Integer, nullable=False),
    Column("overflow_items", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_context_budgets_trace_id", "trace_id"),
    Index("ix_aion_context_budgets_focus_session_id", "focus_session_id"),
    Index("ix_aion_context_budgets_intent_id", "intent_id"),
    Index("ix_aion_context_budgets_context_id", "context_id"),
    Index("ix_aion_context_budgets_created_at", "created_at"),
)

aion_interrupt_records = Table(
    "aion_interrupt_records",
    attention_metadata,
    Column("interrupt_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("focus_session_id", Text, nullable=True),
    Column("interrupt_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("priority_score", Float, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("decision", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_interrupt_records_trace_id", "trace_id"),
    Index("ix_aion_interrupt_records_actor_id", "actor_id"),
    Index("ix_aion_interrupt_records_workspace_id", "workspace_id"),
    Index("ix_aion_interrupt_records_focus_session_id", "focus_session_id"),
    Index("ix_aion_interrupt_records_interrupt_type", "interrupt_type"),
    Index("ix_aion_interrupt_records_source_type", "source_type"),
    Index("ix_aion_interrupt_records_source_id", "source_id"),
    Index("ix_aion_interrupt_records_status", "status"),
    Index("ix_aion_interrupt_records_priority_score", "priority_score"),
    Index("ix_aion_interrupt_records_created_at", "created_at"),
)


class AttentionRepository:
    """Repository for focus, attention, budget, and interrupt records."""

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

    def save_focus_session(self, session: FocusSession) -> FocusSession:
        """Upsert a focus session."""
        self._ensure_schema()
        stored = session.model_copy(
            update={
                "created_at": session.created_at or _now(),
                "updated_at": session.updated_at or _now(),
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_focus_sessions).where(
                    aion_focus_sessions.c.focus_session_id == stored.focus_session_id
                )
            )
            connection.execute(
                insert(aion_focus_sessions).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_focus_session(self, focus_session_id: str) -> FocusSession | None:
        """Return one focus session."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_focus_sessions).where(
                    aion_focus_sessions.c.focus_session_id == focus_session_id
                )
            ).mappings().first()
        return _focus_from_row(row) if row is not None else None

    def get_active_focus(
        self,
        *,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
    ) -> FocusSession | None:
        """Return the newest active focus for an actor/workspace."""
        sessions = self.list_focus_sessions(scope=scope, status="active", limit=200)
        for session in sessions:
            actor_matches = actor_id is None or session.actor_id == actor_id
            workspace_matches = workspace_id is None or session.workspace_id == workspace_id
            if actor_matches and workspace_matches:
                return session
        return None

    def list_focus_sessions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[FocusSession]:
        """List focus sessions visible to a scope."""
        self._ensure_schema()
        statement = select(aion_focus_sessions)
        if status is not None:
            statement = statement.where(aion_focus_sessions.c.status == status)
        statement = statement.order_by(aion_focus_sessions.c.created_at.desc()).limit(limit * 3)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            session
            for session in (_focus_from_row(row) for row in rows)
            if _scope_matches(session.owner_scope, scope)
        ][:limit]

    def save_signal(self, signal: AttentionSignal) -> AttentionSignal:
        """Upsert one attention signal."""
        self._ensure_schema()
        stored = signal.model_copy(update={"created_at": signal.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_attention_signals).where(
                    aion_attention_signals.c.attention_signal_id == stored.attention_signal_id
                )
            )
            connection.execute(
                insert(aion_attention_signals).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_signal(self, attention_signal_id: str) -> AttentionSignal | None:
        """Return one attention signal."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_attention_signals).where(
                    aion_attention_signals.c.attention_signal_id == attention_signal_id
                )
            ).mappings().first()
        return _signal_from_row(row) if row is not None else None

    def list_signals(
        self,
        *,
        scope: list[str],
        handled: bool | None = None,
        limit: int = 100,
    ) -> list[AttentionSignal]:
        """List attention signals visible to a scope."""
        self._ensure_schema()
        statement = select(aion_attention_signals)
        if handled is True:
            statement = statement.where(aion_attention_signals.c.handled_at.is_not(None))
        if handled is False:
            statement = statement.where(aion_attention_signals.c.handled_at.is_(None))
        statement = statement.order_by(aion_attention_signals.c.created_at.desc()).limit(limit * 3)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            signal
            for signal in (_signal_from_row(row) for row in rows)
            if _scope_matches(signal.owner_scope, scope)
        ][:limit]

    def save_decision(self, decision: AttentionDecision) -> AttentionDecision:
        """Persist one attention decision."""
        self._ensure_schema()
        stored = decision.model_copy(update={"created_at": decision.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_attention_decisions).values(**stored.model_dump(mode="python"))
            )
        return stored

    def save_context_budget(self, budget: ContextBudget) -> ContextBudget:
        """Persist one context budget."""
        self._ensure_schema()
        stored = budget.model_copy(update={"created_at": budget.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_context_budgets).where(
                    aion_context_budgets.c.context_budget_id == stored.context_budget_id
                )
            )
            connection.execute(
                insert(aion_context_budgets).values(**stored.model_dump(mode="python"))
            )
        return stored

    def save_interrupt(self, interrupt: InterruptRecord) -> InterruptRecord:
        """Upsert one interrupt."""
        self._ensure_schema()
        stored = interrupt.model_copy(update={"created_at": interrupt.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_interrupt_records).where(
                    aion_interrupt_records.c.interrupt_id == stored.interrupt_id
                )
            )
            connection.execute(
                insert(aion_interrupt_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_interrupt(self, interrupt_id: str) -> InterruptRecord | None:
        """Return one interrupt."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_interrupt_records).where(
                    aion_interrupt_records.c.interrupt_id == interrupt_id
                )
            ).mappings().first()
        return _interrupt_from_row(row) if row is not None else None

    def list_interrupts(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[InterruptRecord]:
        """List interrupts visible to a scope."""
        self._ensure_schema()
        statement = select(aion_interrupt_records)
        if status is not None:
            statement = statement.where(aion_interrupt_records.c.status == status)
        statement = statement.order_by(aion_interrupt_records.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_interrupt_from_row(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        attention_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _focus_from_row(row: RowMapping) -> FocusSession:
    return FocusSession(
        focus_session_id=str(row["focus_session_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(FocusStatus, str(row["status"])),
        focus_type=cast(FocusType, str(row["focus_type"])),
        active_goal_id=_optional_str(row["active_goal_id"]),
        active_task_id=_optional_str(row["active_task_id"]),
        active_workflow_run_id=_optional_str(row["active_workflow_run_id"]),
        active_trace_id=_optional_str(row["active_trace_id"]),
        owner_scope=_list_str(row["owner_scope"]),
        title=str(row["title"]),
        description=str(row["description"]),
        constraints=_list_str(row["constraints"]),
        metadata=_dict(row["metadata"]),
        started_at=_optional_datetime(row["started_at"]),
        paused_at=_optional_datetime(row["paused_at"]),
        ended_at=_optional_datetime(row["ended_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _signal_from_row(row: RowMapping) -> AttentionSignal:
    return AttentionSignal(
        attention_signal_id=str(row["attention_signal_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        signal_type=cast(AttentionSignalType, str(row["signal_type"])),
        source_type=str(row["source_type"]),
        source_id=_optional_str(row["source_id"]),
        title=str(row["title"]),
        payload=_dict(row["payload"]),
        urgency=float(row["urgency"]),
        importance=float(row["importance"]),
        confidence=float(row["confidence"]),
        risk_level=cast(Any, str(row["risk_level"])),
        owner_scope=_list_str(row["owner_scope"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        handled_at=_optional_datetime(row["handled_at"]),
    )


def _decision_from_row(row: RowMapping) -> AttentionDecision:
    return AttentionDecision(
        attention_decision_id=str(row["attention_decision_id"]),
        trace_id=_optional_str(row["trace_id"]),
        focus_session_id=_optional_str(row["focus_session_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        decision_type=cast(AttentionDecisionType, str(row["decision_type"])),
        selected_signal_ids=_list_str(row["selected_signal_ids"]),
        selected_slot_ids=_list_str(row["selected_slot_ids"]),
        selected_memory_ids=_list_str(row["selected_memory_ids"]),
        selected_evidence_ids=_list_str(row["selected_evidence_ids"]),
        selected_skill_ids=_list_str(row["selected_skill_ids"]),
        selected_capability_ids=_list_str(row["selected_capability_ids"]),
        priority_score=float(row["priority_score"]),
        reason=str(row["reason"]),
        constraints=_list_str(row["constraints"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _budget_from_row(row: RowMapping) -> ContextBudget:
    return ContextBudget(
        context_budget_id=str(row["context_budget_id"]),
        trace_id=_optional_str(row["trace_id"]),
        focus_session_id=_optional_str(row["focus_session_id"]),
        intent_id=_optional_str(row["intent_id"]),
        context_id=_optional_str(row["context_id"]),
        max_items=int(row["max_items"]),
        max_chars=int(row["max_chars"]),
        allocation=_dict_int(row["allocation"]),
        used_items=int(row["used_items"]),
        used_chars=int(row["used_chars"]),
        overflow_items=_list_dict(row["overflow_items"]),
        constraints=_list_str(row["constraints"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _interrupt_from_row(row: RowMapping) -> InterruptRecord:
    return InterruptRecord(
        interrupt_id=str(row["interrupt_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        focus_session_id=_optional_str(row["focus_session_id"]),
        interrupt_type=cast(InterruptType, str(row["interrupt_type"])),
        source_type=str(row["source_type"]),
        source_id=_optional_str(row["source_id"]),
        status=cast(InterruptStatus, str(row["status"])),
        priority_score=float(row["priority_score"]),
        payload=_dict(row["payload"]),
        decision=_dict(row["decision"]),
        created_at=_optional_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _dict_int(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): int(amount) for key, amount in value.items()}


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _list_dict(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _now() -> datetime:
    return datetime.now(UTC)
