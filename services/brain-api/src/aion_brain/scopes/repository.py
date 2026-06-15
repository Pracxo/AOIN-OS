"""Persistent scope resolution repository."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Index, MetaData, Table, Text, create_engine, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.scopes import ScopeResolution

scope_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_scope_resolution_records = Table(
    "aion_scope_resolution_records",
    scope_metadata,
    Column("scope_resolution_id", Text, primary_key=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("requested_scopes", json_payload_type, nullable=False),
    Column("resolved_scopes", json_payload_type, nullable=False),
    Column("permissions", json_payload_type, nullable=False),
    Column("decision", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_scope_resolution_records_actor_id", "actor_id"),
    Index("ix_aion_scope_resolution_records_workspace_id", "workspace_id"),
    Index("ix_aion_scope_resolution_records_created_at", "created_at"),
)


class ScopeRepository:
    """Repository for scope resolution audit records."""

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

    def save(self, resolution: ScopeResolution) -> ScopeResolution:
        """Persist a scope resolution."""
        self._ensure_schema()
        stored = resolution.model_copy(
            update={"created_at": resolution.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_scope_resolution_records).values(
                    scope_resolution_id=stored.scope_resolution_id,
                    actor_id=stored.actor_id,
                    workspace_id=stored.workspace_id,
                    requested_scopes=stored.requested_scopes,
                    resolved_scopes=stored.resolved_scopes,
                    permissions=stored.permissions,
                    decision={
                        "allow": stored.allow,
                        "constraints": stored.constraints,
                    },
                    created_at=stored.created_at,
                )
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        scope_metadata.create_all(self._engine)
        self._schema_ready = True
