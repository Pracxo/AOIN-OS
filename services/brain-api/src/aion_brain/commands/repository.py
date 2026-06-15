"""Persistence for AION Brain commands."""

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
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.commands import (
    BrainCommand,
    CommandMode,
    CommandStatus,
    CommandTargetType,
    CommandType,
)

commands_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_commands = Table(
    "aion_commands",
    commands_metadata,
    Column("command_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("idempotency_key", Text, nullable=True, unique=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("command_type", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_commands_trace_id", "trace_id"),
    Index("ix_aion_commands_correlation_id", "correlation_id"),
    Index("ix_aion_commands_idempotency_key", "idempotency_key"),
    Index("ix_aion_commands_actor_id", "actor_id"),
    Index("ix_aion_commands_workspace_id", "workspace_id"),
    Index("ix_aion_commands_command_type", "command_type"),
    Index("ix_aion_commands_target_type", "target_type"),
    Index("ix_aion_commands_mode", "mode"),
    Index("ix_aion_commands_status", "status"),
    Index("ix_aion_commands_created_at", "created_at"),
)


class CommandRepository:
    """Repository for command records."""

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

    def save(self, command: BrainCommand) -> BrainCommand:
        """Create or replace one command record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = command.model_copy(
            update={
                "created_at": command.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_commands).where(aion_commands.c.command_id == stored.command_id)
            )
            connection.execute(insert(aion_commands).values(**stored.model_dump(mode="python")))
        return stored

    def get(self, command_id: str) -> BrainCommand | None:
        """Return one command by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_commands).where(aion_commands.c.command_id == command_id)
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_command(row)

    def get_by_idempotency_key(self, idempotency_key: str) -> BrainCommand | None:
        """Return one command by idempotency key."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_commands).where(
                        aion_commands.c.idempotency_key == idempotency_key
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_command(row)

    def list(
        self,
        *,
        status: str | None = None,
        command_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> list[BrainCommand]:
        """List recent command records."""
        self._ensure_schema()
        statement = select(aion_commands).order_by(aion_commands.c.created_at.desc()).limit(limit)
        if status is not None:
            statement = statement.where(aion_commands.c.status == status)
        if command_type is not None:
            statement = statement.where(aion_commands.c.command_type == command_type)
        if trace_id is not None:
            statement = statement.where(aion_commands.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_command(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        commands_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_command(row: RowMapping) -> BrainCommand:
    return BrainCommand(
        command_id=str(row["command_id"]),
        trace_id=_optional_str(row["trace_id"]),
        correlation_id=_optional_str(row["correlation_id"]),
        idempotency_key=_optional_str(row["idempotency_key"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        command_type=cast(CommandType, str(row["command_type"])),
        target_type=cast(CommandTargetType, str(row["target_type"])),
        target_id=_optional_str(row["target_id"]),
        mode=cast(CommandMode, str(row["mode"])),
        status=cast(CommandStatus, str(row["status"])),
        payload=_dict(row["payload"]),
        result=_dict(row["result"]),
        error=_dict(row["error"]),
        policy_decision_id=_optional_str(row["policy_decision_id"]),
        autonomy_decision_id=_optional_str(row["autonomy_decision_id"]),
        risk_assessment_id=_optional_str(row["risk_assessment_id"]),
        approval_request_id=_optional_str(row["approval_request_id"]),
        created_at=_datetime(row["created_at"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        updated_at=_datetime(row["updated_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


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
