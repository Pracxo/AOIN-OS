"""Persistence for event reaction subscriptions, dispatches, actions, and dead letters."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
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

from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDeadLetterStatus,
    EventDispatchRecord,
    EventDispatchStatus,
    EventReactionAction,
    EventReactionActionStatus,
    EventReactionMode,
    EventReactionRiskLevel,
    EventReactionTargetType,
    EventSubscription,
    EventSubscriptionStatus,
    EventTriggerRule,
)

event_reaction_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_event_subscriptions = Table(
    "aion_event_subscriptions",
    event_reaction_metadata,
    Column("subscription_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_filters", json_payload_type, nullable=False),
    Column("event_type_patterns", json_payload_type, nullable=False),
    Column("trigger_rules", json_payload_type, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("reaction_mode", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("max_actions", Integer, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_event_subscriptions_status", "status"),
    Index("ix_aion_event_subscriptions_target_type", "target_type"),
    Index("ix_aion_event_subscriptions_created_at", "created_at"),
)

aion_event_dispatch_records = Table(
    "aion_event_dispatch_records",
    event_reaction_metadata,
    Column("dispatch_id", Text, primary_key=True),
    Column("event_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("matched_subscription_ids", json_payload_type, nullable=False),
    Column("actions", json_payload_type, nullable=False),
    Column("action_count", Integer, nullable=False),
    Column("completed_action_count", Integer, nullable=False),
    Column("failed_action_count", Integer, nullable=False),
    Column("blocked_action_count", Integer, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_event_dispatch_records_event_id", "event_id"),
    Index("ix_aion_event_dispatch_records_trace_id", "trace_id"),
    Index("ix_aion_event_dispatch_records_workspace_id", "workspace_id"),
    Index("ix_aion_event_dispatch_records_status", "status"),
    Index("ix_aion_event_dispatch_records_created_at", "created_at"),
)

aion_event_reaction_actions = Table(
    "aion_event_reaction_actions",
    event_reaction_metadata,
    Column("reaction_action_id", Text, primary_key=True),
    Column(
        "dispatch_id",
        Text,
        ForeignKey("aion_event_dispatch_records.dispatch_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("subscription_id", Text, nullable=False),
    Column("event_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("action_type", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_event_reaction_actions_dispatch_id", "dispatch_id"),
    Index("ix_aion_event_reaction_actions_subscription_id", "subscription_id"),
    Index("ix_aion_event_reaction_actions_event_id", "event_id"),
    Index("ix_aion_event_reaction_actions_trace_id", "trace_id"),
    Index("ix_aion_event_reaction_actions_status", "status"),
    Index("ix_aion_event_reaction_actions_target_type", "target_type"),
    Index("ix_aion_event_reaction_actions_created_at", "created_at"),
)

aion_event_dead_letters = Table(
    "aion_event_dead_letters",
    event_reaction_metadata,
    Column("dead_letter_id", Text, primary_key=True),
    Column("dispatch_id", Text, nullable=False),
    Column("reaction_action_id", Text, nullable=True),
    Column("event_id", Text, nullable=False),
    Column("subscription_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("replay_count", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_event_dead_letters_event_id", "event_id"),
    Index("ix_aion_event_dead_letters_subscription_id", "subscription_id"),
    Index("ix_aion_event_dead_letters_trace_id", "trace_id"),
    Index("ix_aion_event_dead_letters_status", "status"),
    Index("ix_aion_event_dead_letters_created_at", "created_at"),
)


class EventReactionRepository:
    """Repository for the event reaction control plane."""

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

    def save_subscription(self, subscription: EventSubscription) -> EventSubscription:
        """Create or replace a subscription."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = subscription.model_copy(
            update={
                "created_at": subscription.created_at or now,
                "updated_at": now,
            }
        )
        values = stored.model_dump(mode="python")
        values["trigger_rules"] = [rule.model_dump(mode="json") for rule in stored.trigger_rules]
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_event_subscriptions).where(
                    aion_event_subscriptions.c.subscription_id == stored.subscription_id
                )
            )
            connection.execute(insert(aion_event_subscriptions).values(**values))
        return stored

    def get_subscription(self, subscription_id: str) -> EventSubscription | None:
        """Return one subscription."""
        self._ensure_schema()
        statement = select(aion_event_subscriptions).where(
            aion_event_subscriptions.c.subscription_id == subscription_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return None if row is None else _row_to_subscription(row)

    def list_subscriptions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
    ) -> list[EventSubscription]:
        """List subscriptions visible to the requested scope."""
        self._ensure_schema()
        statement = select(aion_event_subscriptions).order_by(
            aion_event_subscriptions.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_event_subscriptions.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            subscription
            for subscription in (_row_to_subscription(row) for row in rows)
            if _scope_matches(subscription.owner_scope, scope)
        ]

    def save_dispatch(self, record: EventDispatchRecord) -> EventDispatchRecord:
        """Create or replace a dispatch record."""
        self._ensure_schema()
        stored = record.model_copy(update={"created_at": record.created_at or datetime.now(UTC)})
        values = stored.model_dump(mode="python")
        values["matched_subscription_ids"] = list(stored.matched_subscription_ids)
        values["actions"] = [action.model_dump(mode="json") for action in stored.actions]
        values["result"] = stored.result
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_event_dispatch_records).where(
                    aion_event_dispatch_records.c.dispatch_id == stored.dispatch_id
                )
            )
            connection.execute(insert(aion_event_dispatch_records).values(**values))
        return stored

    def get_dispatch(self, dispatch_id: str) -> EventDispatchRecord | None:
        """Return one dispatch record."""
        self._ensure_schema()
        statement = select(aion_event_dispatch_records).where(
            aion_event_dispatch_records.c.dispatch_id == dispatch_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return None if row is None else _row_to_dispatch(row)

    def list_dispatches(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[EventDispatchRecord]:
        """List recent dispatch records."""
        self._ensure_schema()
        statement = select(aion_event_dispatch_records).order_by(
            aion_event_dispatch_records.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_event_dispatch_records.c.status == status)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            record
            for record in (_row_to_dispatch(row) for row in rows)
            if _scope_matches(_owner_scope_from_result(record.result), scope)
        ]

    def save_action(self, action: EventReactionAction) -> EventReactionAction:
        """Create or replace an action record."""
        self._ensure_schema()
        stored = action.model_copy(update={"created_at": action.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_event_reaction_actions).where(
                    aion_event_reaction_actions.c.reaction_action_id == stored.reaction_action_id
                )
            )
            connection.execute(
                insert(aion_event_reaction_actions).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_actions(self, dispatch_id: str) -> list[EventReactionAction]:
        """Return actions for one dispatch."""
        self._ensure_schema()
        statement = (
            select(aion_event_reaction_actions)
            .where(aion_event_reaction_actions.c.dispatch_id == dispatch_id)
            .order_by(aion_event_reaction_actions.c.created_at)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_action(row) for row in rows]

    def save_dead_letter(self, record: EventDeadLetterRecord) -> EventDeadLetterRecord:
        """Create or replace a dead-letter record."""
        self._ensure_schema()
        stored = record.model_copy(update={"created_at": record.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_event_dead_letters).where(
                    aion_event_dead_letters.c.dead_letter_id == stored.dead_letter_id
                )
            )
            connection.execute(
                insert(aion_event_dead_letters).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_dead_letter(self, dead_letter_id: str) -> EventDeadLetterRecord | None:
        """Return one dead letter."""
        self._ensure_schema()
        statement = select(aion_event_dead_letters).where(
            aion_event_dead_letters.c.dead_letter_id == dead_letter_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return None if row is None else _row_to_dead_letter(row)

    def list_dead_letters(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[EventDeadLetterRecord]:
        """List dead-letter records."""
        self._ensure_schema()
        statement = select(aion_event_dead_letters).order_by(
            aion_event_dead_letters.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_event_dead_letters.c.status == status)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            record
            for record in (_row_to_dead_letter(row) for row in rows)
            if _scope_matches(_owner_scope_from_result(record.error), scope)
        ]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        event_reaction_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_subscription(row: RowMapping) -> EventSubscription:
    trigger_rules = [EventTriggerRule.model_validate(rule) for rule in _list(row["trigger_rules"])]
    return EventSubscription(
        subscription_id=str(row["subscription_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(EventSubscriptionStatus, str(row["status"])),
        owner_scope=[str(item) for item in _list(row["owner_scope"])],
        source_filters=[str(item) for item in _list(row["source_filters"])],
        event_type_patterns=[str(item) for item in _list(row["event_type_patterns"])],
        trigger_rules=trigger_rules,
        target_type=cast(EventReactionTargetType, str(row["target_type"])),
        target_id=_optional_str(row["target_id"]),
        reaction_mode=cast(EventReactionMode, str(row["reaction_mode"])),
        risk_level=cast(EventReactionRiskLevel, str(row["risk_level"])),
        max_actions=int(row["max_actions"]),
        constraints=[str(item) for item in _list(row["constraints"])],
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_dispatch(row: RowMapping) -> EventDispatchRecord:
    actions = [EventReactionAction.model_validate(action) for action in _list(row["actions"])]
    return EventDispatchRecord(
        dispatch_id=str(row["dispatch_id"]),
        event_id=str(row["event_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(EventDispatchStatus, str(row["status"])),
        mode=cast(EventReactionMode, str(row["mode"])),
        matched_subscription_ids=[str(item) for item in _list(row["matched_subscription_ids"])],
        actions=actions,
        action_count=int(row["action_count"]),
        completed_action_count=int(row["completed_action_count"]),
        failed_action_count=int(row["failed_action_count"]),
        blocked_action_count=int(row["blocked_action_count"]),
        result=_dict(row["result"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_action(row: RowMapping) -> EventReactionAction:
    return EventReactionAction(
        reaction_action_id=str(row["reaction_action_id"]),
        dispatch_id=str(row["dispatch_id"]),
        subscription_id=str(row["subscription_id"]),
        event_id=str(row["event_id"]),
        trace_id=_optional_str(row["trace_id"]),
        target_type=cast(EventReactionTargetType, str(row["target_type"])),
        target_id=_optional_str(row["target_id"]),
        action_type=str(row["action_type"]),
        mode=cast(EventReactionMode, str(row["mode"])),
        status=cast(EventReactionActionStatus, str(row["status"])),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        policy_decision_id=_optional_str(row["policy_decision_id"]),
        risk_assessment_id=_optional_str(row["risk_assessment_id"]),
        approval_request_id=_optional_str(row["approval_request_id"]),
        autonomy_decision_id=_optional_str(row["autonomy_decision_id"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_dead_letter(row: RowMapping) -> EventDeadLetterRecord:
    return EventDeadLetterRecord(
        dead_letter_id=str(row["dead_letter_id"]),
        dispatch_id=str(row["dispatch_id"]),
        reaction_action_id=_optional_str(row["reaction_action_id"]),
        event_id=str(row["event_id"]),
        subscription_id=_optional_str(row["subscription_id"]),
        trace_id=_optional_str(row["trace_id"]),
        reason=str(row["reason"]),
        error=_dict(row["error"]),
        status=cast(EventDeadLetterStatus, str(row["status"])),
        replay_count=int(row["replay_count"]),
        created_at=_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    if not requested_scope:
        return True
    return bool(set(owner_scope).intersection(requested_scope))


def _owner_scope_from_result(result: dict[str, Any]) -> list[str]:
    owner_scope = result.get("owner_scope")
    if isinstance(owner_scope, list):
        return [str(item) for item in owner_scope]
    return ["workspace:main"]


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    raise TypeError("Expected datetime-compatible value")
