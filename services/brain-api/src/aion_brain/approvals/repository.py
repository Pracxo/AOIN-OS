"""Approval control-plane persistence."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
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

from aion_brain.contracts.approvals import (
    ApprovalDecision,
    ApprovalInboxQuery,
    ApprovalLifecycleEvent,
    ApprovalLifecycleEventType,
    ApprovalPriority,
    ApprovalRequest,
    ApprovalStatus,
)

approval_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_approval_requests = Table(
    "aion_approval_requests",
    approval_metadata,
    Column("approval_request_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("requested_by", Text, nullable=True),
    Column("assigned_to", Text, nullable=True),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("risk_assessment_id", Text, nullable=True),
    Column("guardrail_decision_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("priority", Text, nullable=False),
    Column("approval_scope", json_payload_type, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_approval_requests_trace_id", "trace_id"),
    Index("ix_aion_approval_requests_actor_id", "actor_id"),
    Index("ix_aion_approval_requests_workspace_id", "workspace_id"),
    Index("ix_aion_approval_requests_requested_by", "requested_by"),
    Index("ix_aion_approval_requests_assigned_to", "assigned_to"),
    Index("ix_aion_approval_requests_action_type", "action_type"),
    Index("ix_aion_approval_requests_resource_type", "resource_type"),
    Index("ix_aion_approval_requests_resource_id", "resource_id"),
    Index("ix_aion_approval_requests_status", "status"),
    Index("ix_aion_approval_requests_priority", "priority"),
    Index("ix_aion_approval_requests_expires_at", "expires_at"),
    Index("ix_aion_approval_requests_created_at", "created_at"),
)

aion_approval_decisions = Table(
    "aion_approval_decisions",
    approval_metadata,
    Column("approval_decision_id", Text, primary_key=True),
    Column("approval_request_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("decided_by", Text, nullable=True),
    Column("decision", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("decision_payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_approval_decisions_approval_request_id", "approval_request_id"),
    Index("ix_aion_approval_decisions_trace_id", "trace_id"),
    Index("ix_aion_approval_decisions_decided_by", "decided_by"),
    Index("ix_aion_approval_decisions_decision", "decision"),
    Index("ix_aion_approval_decisions_created_at", "created_at"),
)

aion_approval_lifecycle_events = Table(
    "aion_approval_lifecycle_events",
    approval_metadata,
    Column("approval_event_id", Text, primary_key=True),
    Column("approval_request_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("from_status", Text, nullable=True),
    Column("to_status", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("reason", Text, nullable=True),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_approval_events_approval_request_id", "approval_request_id"),
    Index("ix_aion_approval_events_trace_id", "trace_id"),
    Index("ix_aion_approval_events_event_type", "event_type"),
    Index("ix_aion_approval_events_actor_id", "actor_id"),
    Index("ix_aion_approval_events_created_at", "created_at"),
)


class ApprovalRepository:
    """Repository for approval requests, decisions, and lifecycle events."""

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

    def save_request(self, request: ApprovalRequest) -> ApprovalRequest:
        """Upsert one approval request."""
        self._ensure_schema()
        values = request.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_approval_requests.c.approval_request_id).where(
                    aion_approval_requests.c.approval_request_id
                    == request.approval_request_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_approval_requests).values(**values))
            else:
                connection.execute(
                    update(aion_approval_requests)
                    .where(
                        aion_approval_requests.c.approval_request_id
                        == request.approval_request_id
                    )
                    .values(**values)
                )
        return request

    def get_request(self, approval_request_id: str) -> ApprovalRequest | None:
        """Return one approval request."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_approval_requests).where(
                    aion_approval_requests.c.approval_request_id == approval_request_id
                )
            ).mappings().first()
        return _request_from_row(row) if row is not None else None

    def list_requests(self, query: ApprovalInboxQuery) -> list[ApprovalRequest]:
        """List approval requests with deterministic filters."""
        self._ensure_schema()
        statement = select(aion_approval_requests)
        if query.status is not None:
            statement = statement.where(aion_approval_requests.c.status == query.status)
        if query.priority is not None:
            statement = statement.where(aion_approval_requests.c.priority == query.priority)
        if query.action_type is not None:
            statement = statement.where(
                aion_approval_requests.c.action_type == query.action_type
            )
        if query.resource_type is not None:
            statement = statement.where(
                aion_approval_requests.c.resource_type == query.resource_type
            )
        if query.actor_id is not None:
            statement = statement.where(aion_approval_requests.c.actor_id == query.actor_id)
        if query.workspace_id is not None:
            statement = statement.where(
                aion_approval_requests.c.workspace_id == query.workspace_id
            )
        statement = statement.order_by(aion_approval_requests.c.created_at.desc()).limit(
            query.limit
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        approvals = [_request_from_row(row) for row in rows]
        return [
            approval
            for approval in approvals
            if _scope_matches(approval.approval_scope, query.scope)
        ][: query.limit]

    def save_decision(self, decision: ApprovalDecision) -> ApprovalDecision:
        """Persist one approval decision."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_approval_decisions).values(**decision.model_dump(mode="python"))
            )
        return decision

    def save_lifecycle_event(
        self,
        event: ApprovalLifecycleEvent,
    ) -> ApprovalLifecycleEvent:
        """Persist one approval lifecycle event."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_approval_lifecycle_events).values(
                    **event.model_dump(mode="python")
                )
            )
        return event

    def list_lifecycle_events(self, approval_request_id: str) -> list[ApprovalLifecycleEvent]:
        """Return lifecycle events for one approval request."""
        self._ensure_schema()
        statement = (
            select(aion_approval_lifecycle_events)
            .where(
                aion_approval_lifecycle_events.c.approval_request_id
                == approval_request_id
            )
            .order_by(aion_approval_lifecycle_events.c.created_at)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_event_from_row(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        approval_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _request_from_row(row: RowMapping) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=str(row["approval_request_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        requested_by=_optional_str(row["requested_by"]),
        assigned_to=_optional_str(row["assigned_to"]),
        action_type=str(row["action_type"]),
        resource_type=str(row["resource_type"]),
        resource_id=_optional_str(row["resource_id"]),
        title=str(row["title"]),
        description=str(row["description"]),
        risk_assessment_id=_optional_str(row["risk_assessment_id"]),
        guardrail_decision_id=_optional_str(row["guardrail_decision_id"]),
        status=cast(ApprovalStatus, str(row["status"])),
        priority=cast(ApprovalPriority, str(row["priority"])),
        approval_scope=_list_str(row["approval_scope"]),
        payload=_dict(row["payload"]),
        constraints=_list_str(row["constraints"]),
        expires_at=_optional_datetime(row["expires_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _event_from_row(row: RowMapping) -> ApprovalLifecycleEvent:
    return ApprovalLifecycleEvent(
        approval_event_id=str(row["approval_event_id"]),
        approval_request_id=str(row["approval_request_id"]),
        trace_id=_optional_str(row["trace_id"]),
        event_type=cast(ApprovalLifecycleEventType, str(row["event_type"])),
        from_status=_optional_str(row["from_status"]),
        to_status=_optional_str(row["to_status"]),
        actor_id=_optional_str(row["actor_id"]),
        reason=_optional_str(row["reason"]),
        payload=_dict(row["payload"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
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


def _scope_matches(approval_scope: list[str], query_scope: list[str]) -> bool:
    return bool(set(approval_scope) & set(query_scope))
