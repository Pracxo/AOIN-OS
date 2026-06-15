"""Persistent repository for metadata-only connector definitions."""

from __future__ import annotations

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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.connectors import (
    ConnectorDefinition,
    ConnectorRiskLevel,
    ConnectorStatus,
    ConnectorType,
)

connector_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_connector_definitions = Table(
    "aion_connector_definitions",
    connector_metadata,
    Column("connector_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("connector_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("base_endpoint_ref", Text, nullable=True),
    Column("auth_secret_ref_id", Text, nullable=True),
    Column("allowed_actions", json_payload_type, nullable=False),
    Column("allowed_scopes", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_connector_definitions_name", "name"),
    Index("ix_aion_connector_definitions_status", "status"),
    Index("ix_aion_connector_definitions_connector_type", "connector_type"),
    Index("ix_aion_connector_definitions_auth_secret_ref_id", "auth_secret_ref_id"),
    Index("ix_aion_connector_definitions_risk_level", "risk_level"),
    Index("ix_aion_connector_definitions_created_at", "created_at"),
)


class ConnectorRepository:
    """Repository for connector definition metadata."""

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
            self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save(self, connector: ConnectorDefinition) -> ConnectorDefinition:
        """Upsert one connector definition."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = connector.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = connector.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_connector_definitions.c.connector_id).where(
                    aion_connector_definitions.c.connector_id == connector.connector_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_connector_definitions).values(**values))
            else:
                connection.execute(
                    update(aion_connector_definitions)
                    .where(aion_connector_definitions.c.connector_id == connector.connector_id)
                    .values(**values)
                )
        return stored

    def get(self, connector_id: str) -> ConnectorDefinition | None:
        """Return one connector definition."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_connector_definitions).where(
                    aion_connector_definitions.c.connector_id == connector_id
                )
            ).mappings().first()
        return _row_to_connector(row) if row is not None else None

    def list(
        self,
        *,
        status: str | None = None,
        connector_type: str | None = None,
    ) -> list[ConnectorDefinition]:
        """List connector definitions."""
        self._ensure_schema()
        statement = select(aion_connector_definitions)
        if status is not None:
            statement = statement.where(aion_connector_definitions.c.status == status)
        if connector_type is not None:
            statement = statement.where(
                aion_connector_definitions.c.connector_type == connector_type
            )
        statement = statement.order_by(aion_connector_definitions.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_connector(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            connector_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_connector(row: RowMapping) -> ConnectorDefinition:
    return ConnectorDefinition(
        connector_id=str(row["connector_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(ConnectorStatus, str(row["status"])),
        connector_type=cast(ConnectorType, str(row["connector_type"])),
        owner_scope=list(row["owner_scope"]),
        base_endpoint_ref=_optional_str(row["base_endpoint_ref"]),
        auth_secret_ref_id=_optional_str(row["auth_secret_ref_id"]),
        allowed_actions=list(row["allowed_actions"]),
        allowed_scopes=list(row["allowed_scopes"]),
        risk_level=cast(ConnectorRiskLevel, str(row["risk_level"])),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"expected datetime-compatible value, got {type(value)!r}")


__all__ = ["ConnectorRepository", "aion_connector_definitions", "connector_metadata"]
