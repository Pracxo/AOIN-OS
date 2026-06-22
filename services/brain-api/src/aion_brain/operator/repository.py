"""Persistence for Operator Control Tower records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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

from aion_brain.contracts.operator import (
    OperatorAcknowledgement,
    OperatorActionItem,
    OperatorSnapshot,
)

operator_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_operator_snapshots = Table(
    "aion_operator_snapshots",
    operator_metadata,
    Column("operator_snapshot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("snapshot_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("overview", json_payload_type, nullable=False),
    Column("action_items", json_payload_type, nullable=False),
    Column("queue_summaries", json_payload_type, nullable=False),
    Column("readiness", json_payload_type, nullable=False),
    Column("generated_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_operator_snapshots_trace_id", "trace_id"),
    Index("ix_aion_operator_snapshots_actor_id", "actor_id"),
    Index("ix_aion_operator_snapshots_workspace_id", "workspace_id"),
    Index("ix_aion_operator_snapshots_snapshot_type", "snapshot_type"),
    Index("ix_aion_operator_snapshots_status", "status"),
    Index("ix_aion_operator_snapshots_created_at", "created_at"),
)

aion_operator_action_items = Table(
    "aion_operator_action_items",
    operator_metadata,
    Column("action_item_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("category", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("runbook_ref", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("acknowledged_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_operator_action_items_trace_id", "trace_id"),
    Index("ix_aion_operator_action_items_source_type", "source_type"),
    Index("ix_aion_operator_action_items_category", "category"),
    Index("ix_aion_operator_action_items_severity", "severity"),
    Index("ix_aion_operator_action_items_status", "status"),
    Index("ix_aion_operator_action_items_created_at", "created_at"),
)

aion_operator_acknowledgements = Table(
    "aion_operator_acknowledgements",
    operator_metadata,
    Column("acknowledgement_id", Text, primary_key=True),
    Column("action_item_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_operator_ack_action_item_id", "action_item_id"),
    Index("ix_aion_operator_ack_source_type", "source_type"),
    Index("ix_aion_operator_ack_source_id", "source_id"),
    Index("ix_aion_operator_ack_actor_id", "actor_id"),
    Index("ix_aion_operator_ack_workspace_id", "workspace_id"),
    Index("ix_aion_operator_ack_created_at", "created_at"),
)


class OperatorRepository:
    """Local repository for operator snapshots, actions, and acknowledgements."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        self._engine = engine or create_engine(
            database_url or "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False}
            if (database_url or "").startswith("sqlite")
            else {},
            poolclass=StaticPool if (database_url or "").startswith("sqlite") else QueuePool,
        )
        self._auto_create = auto_create
        self._schema_ready = False

    def save_action_item(self, item: OperatorActionItem) -> OperatorActionItem:
        """Persist a generated action item if not already present."""
        self._ensure_schema()
        existing = self.get_action_item(item.action_item_id)
        if existing is not None:
            return existing
        values = item.model_dump(mode="python")
        values["created_at"] = item.created_at or datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(insert(aion_operator_action_items).values(**values))
        return OperatorActionItem(**values)

    def get_action_item(self, action_item_id: str) -> OperatorActionItem | None:
        """Return one action item."""
        self._ensure_schema()
        statement = select(aion_operator_action_items).where(
            aion_operator_action_items.c.action_item_id == action_item_id
        )
        row = self._first(statement)
        return _row_to_action_item(row) if row is not None else None

    def list_action_items(
        self,
        *,
        status: str | None = None,
        source_type: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionItem]:
        """List local action items."""
        self._ensure_schema()
        statement = select(aion_operator_action_items).order_by(
            aion_operator_action_items.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_operator_action_items.c.status == status)
        if source_type is not None:
            statement = statement.where(aion_operator_action_items.c.source_type == source_type)
        rows = self._list(statement.limit(limit))
        return [_row_to_action_item(row) for row in rows]

    def acknowledge_action_item(
        self,
        action_item_id: str,
        *,
        acknowledged_at: datetime | None = None,
    ) -> OperatorActionItem | None:
        """Mark the local operator item acknowledged without resolving its source."""
        self._ensure_schema()
        timestamp = acknowledged_at or datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_operator_action_items)
                .where(aion_operator_action_items.c.action_item_id == action_item_id)
                .values(status="acknowledged", acknowledged_at=timestamp)
            )
        return self.get_action_item(action_item_id)

    def save_acknowledgement(
        self,
        acknowledgement: OperatorAcknowledgement,
    ) -> OperatorAcknowledgement:
        """Persist an operator acknowledgement."""
        self._ensure_schema()
        values = acknowledgement.model_dump(mode="python")
        values["created_at"] = acknowledgement.created_at or datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(insert(aion_operator_acknowledgements).values(**values))
        return OperatorAcknowledgement(**values)

    def list_acknowledgements(
        self,
        *,
        source_type: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> list[OperatorAcknowledgement]:
        """List acknowledgement records."""
        self._ensure_schema()
        statement = select(aion_operator_acknowledgements).order_by(
            aion_operator_acknowledgements.c.created_at.desc()
        )
        if source_type is not None:
            statement = statement.where(aion_operator_acknowledgements.c.source_type == source_type)
        if source_id is not None:
            statement = statement.where(aion_operator_acknowledgements.c.source_id == source_id)
        return [_row_to_acknowledgement(row) for row in self._list(statement.limit(limit))]

    def save_snapshot(self, snapshot: OperatorSnapshot) -> OperatorSnapshot:
        """Persist a local operator snapshot."""
        self._ensure_schema()
        values = snapshot.model_dump(mode="python", exclude={"created_at"})
        values["created_at"] = snapshot.created_at or datetime.now(UTC)
        values["overview"] = snapshot.overview.model_dump(mode="json")
        values["action_items"] = [item.model_dump(mode="json") for item in snapshot.action_items]
        values["queue_summaries"] = [
            queue.model_dump(mode="json") for queue in snapshot.queue_summaries
        ]
        values["readiness"] = (
            snapshot.readiness.model_dump(mode="json") if snapshot.readiness else {}
        )
        with self._engine.begin() as connection:
            connection.execute(insert(aion_operator_snapshots).values(**values))
        return _snapshot_from_values(values)

    def get_snapshot(self, operator_snapshot_id: str) -> OperatorSnapshot | None:
        """Return one snapshot."""
        self._ensure_schema()
        statement = select(aion_operator_snapshots).where(
            aion_operator_snapshots.c.operator_snapshot_id == operator_snapshot_id
        )
        row = self._first(statement)
        return _row_to_snapshot(row) if row is not None else None

    def list_snapshots(
        self,
        *,
        scope: list[str],
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[OperatorSnapshot]:
        """List snapshots visible to a scope."""
        self._ensure_schema()
        statement = select(aion_operator_snapshots).order_by(
            aion_operator_snapshots.c.created_at.desc()
        )
        if snapshot_type is not None:
            statement = statement.where(aion_operator_snapshots.c.snapshot_type == snapshot_type)
        if status is not None:
            statement = statement.where(aion_operator_snapshots.c.status == status)
        snapshots = [_row_to_snapshot(row) for row in self._list(statement.limit(limit))]
        return [snapshot for snapshot in snapshots if _scope_matches(snapshot.owner_scope, scope)]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        operator_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _list(self, statement: Any) -> list[RowMapping]:
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())


def _row_to_action_item(row: RowMapping) -> OperatorActionItem:
    return OperatorActionItem(**dict(row))


def _row_to_acknowledgement(row: RowMapping) -> OperatorAcknowledgement:
    return OperatorAcknowledgement(**dict(row))


def _row_to_snapshot(row: RowMapping) -> OperatorSnapshot:
    return _snapshot_from_values(dict(row))


def _snapshot_from_values(values: dict[str, Any]) -> OperatorSnapshot:
    payload = dict(values)
    payload["readiness"] = payload["readiness"] or None
    return OperatorSnapshot.model_validate(payload)


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))
