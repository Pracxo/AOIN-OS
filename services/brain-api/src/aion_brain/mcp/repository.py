"""MCP adapter metadata repository."""

from __future__ import annotations

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
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.mcp import (
    MCPCapabilityMapping,
    MCPHealthStatus,
    MCPInvocationResult,
    MCPMappingStatus,
    MCPRiskLevel,
    MCPServerHealth,
    MCPServerRecord,
    MCPServerStatus,
    MCPSyncResponse,
    MCPTransportType,
)

mcp_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_mcp_servers = Table(
    "aion_mcp_servers",
    mcp_metadata,
    Column("mcp_server_id", Text, primary_key=True),
    Column("server_name", Text, nullable=False),
    Column("transport_type", Text, nullable=False),
    Column("endpoint_ref", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("health_status", Text, nullable=False),
    Column("config", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_health_check_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_mcp_servers_server_name", "server_name"),
    Index("ix_aion_mcp_servers_transport_type", "transport_type"),
    Index("ix_aion_mcp_servers_status", "status"),
    Index("ix_aion_mcp_servers_health_status", "health_status"),
    Index("ix_aion_mcp_servers_created_at", "created_at"),
)

aion_mcp_capability_mappings = Table(
    "aion_mcp_capability_mappings",
    mcp_metadata,
    Column("mapping_id", Text, primary_key=True),
    Column(
        "mcp_server_id",
        Text,
        ForeignKey("aion_mcp_servers.mcp_server_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("mcp_tool_name", Text, nullable=False),
    Column("capability_id", Text, nullable=False),
    Column("module_id", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("input_schema", json_payload_type, nullable=False),
    Column("output_schema", json_payload_type, nullable=False),
    Column("permissions_required", json_payload_type, nullable=False),
    Column("memory_read_scopes", json_payload_type, nullable=False),
    Column("memory_write_scopes", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("mcp_server_id", "mcp_tool_name", name="uq_mcp_server_tool"),
    UniqueConstraint("capability_id", name="uq_mcp_capability_id"),
    Index("ix_aion_mcp_mappings_server", "mcp_server_id"),
    Index("ix_aion_mcp_mappings_tool", "mcp_tool_name"),
    Index("ix_aion_mcp_mappings_capability", "capability_id"),
    Index("ix_aion_mcp_mappings_module", "module_id"),
    Index("ix_aion_mcp_mappings_risk", "risk_level"),
    Index("ix_aion_mcp_mappings_status", "status"),
    Index("ix_aion_mcp_mappings_created_at", "created_at"),
)

aion_mcp_sync_records = Table(
    "aion_mcp_sync_records",
    mcp_metadata,
    Column("sync_id", Text, primary_key=True),
    Column("mcp_server_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("discovered_tools", Integer, nullable=False),
    Column("mapped_capabilities", Integer, nullable=False),
    Column("skipped", Integer, nullable=False),
    Column("failed", Integer, nullable=False),
    Column("errors", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_mcp_sync_server", "mcp_server_id"),
    Index("ix_aion_mcp_sync_status", "status"),
    Index("ix_aion_mcp_sync_created_at", "created_at"),
)

aion_mcp_invocation_records = Table(
    "aion_mcp_invocation_records",
    mcp_metadata,
    Column("mcp_invocation_id", Text, primary_key=True),
    Column("invocation_id", Text, nullable=True),
    Column("mcp_server_id", Text, nullable=False),
    Column("mcp_tool_name", Text, nullable=False),
    Column("capability_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("execution_id", Text, nullable=True),
    Column("step_run_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("request", json_payload_type, nullable=False),
    Column("response", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("policy_decision_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_mcp_invocation_invocation", "invocation_id"),
    Index("ix_aion_mcp_invocation_server", "mcp_server_id"),
    Index("ix_aion_mcp_invocation_tool", "mcp_tool_name"),
    Index("ix_aion_mcp_invocation_capability", "capability_id"),
    Index("ix_aion_mcp_invocation_trace", "trace_id"),
    Index("ix_aion_mcp_invocation_execution", "execution_id"),
    Index("ix_aion_mcp_invocation_status", "status"),
    Index("ix_aion_mcp_invocation_created_at", "created_at"),
)


class MCPRepository:
    """Repository for MCP server, mapping, sync, and invocation metadata."""

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
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(
                    database_url,
                    poolclass=QueuePool,
                    pool_pre_ping=True,
                )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def create_server(self, server: MCPServerRecord) -> MCPServerRecord:
        """Upsert an MCP server record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = server.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = server.model_copy(update={"created_at": values["created_at"], "updated_at": now})
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_mcp_servers.c.mcp_server_id).where(
                    aion_mcp_servers.c.mcp_server_id == server.mcp_server_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_mcp_servers).values(**values))
            else:
                connection.execute(
                    update(aion_mcp_servers)
                    .where(aion_mcp_servers.c.mcp_server_id == server.mcp_server_id)
                    .values(**values)
                )
        return stored

    def get_server(self, mcp_server_id: str) -> MCPServerRecord | None:
        """Return one MCP server."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_mcp_servers).where(
                        aion_mcp_servers.c.mcp_server_id == mcp_server_id
                    )
                )
                .mappings()
                .first()
            )
        return _server_from_row(row) if row is not None else None

    def list_servers(self, status: str | None = None) -> list[MCPServerRecord]:
        """List MCP servers."""
        self._ensure_schema()
        statement = select(aion_mcp_servers)
        if status is not None:
            statement = statement.where(aion_mcp_servers.c.status == status)
        statement = statement.order_by(aion_mcp_servers.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_server_from_row(row) for row in rows]

    def disable_server(
        self,
        mcp_server_id: str,
        reason: str | None = None,
    ) -> MCPServerRecord:
        """Disable one MCP server."""
        server = self.get_server(mcp_server_id)
        if server is None:
            raise KeyError(mcp_server_id)
        disabled = server.model_copy(
            update={
                "status": "disabled",
                "disabled_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "config": {**server.config, "disabled_reason": reason} if reason else server.config,
            }
        )
        return self.create_server(disabled)

    def upsert_mapping(self, mapping: MCPCapabilityMapping) -> MCPCapabilityMapping:
        """Upsert an MCP capability mapping."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = mapping.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = mapping.model_copy(update={"created_at": values["created_at"], "updated_at": now})
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_mcp_capability_mappings.c.mapping_id).where(
                    aion_mcp_capability_mappings.c.mapping_id == mapping.mapping_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_mcp_capability_mappings).values(**values))
            else:
                connection.execute(
                    update(aion_mcp_capability_mappings)
                    .where(aion_mcp_capability_mappings.c.mapping_id == mapping.mapping_id)
                    .values(**values)
                )
        return stored

    def get_mapping_by_capability(self, capability_id: str) -> MCPCapabilityMapping | None:
        """Return a mapping by AION capability ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_mcp_capability_mappings).where(
                        aion_mcp_capability_mappings.c.capability_id == capability_id
                    )
                )
                .mappings()
                .first()
            )
        return _mapping_from_row(row) if row is not None else None

    def get_mapping_by_tool(
        self,
        mcp_server_id: str,
        tool_name: str,
    ) -> MCPCapabilityMapping | None:
        """Return a mapping by MCP server and tool name."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_mcp_capability_mappings)
                    .where(aion_mcp_capability_mappings.c.mcp_server_id == mcp_server_id)
                    .where(aion_mcp_capability_mappings.c.mcp_tool_name == tool_name)
                )
                .mappings()
                .first()
            )
        return _mapping_from_row(row) if row is not None else None

    def list_mappings(
        self,
        mcp_server_id: str | None = None,
        status: str | None = None,
    ) -> list[MCPCapabilityMapping]:
        """List MCP capability mappings."""
        self._ensure_schema()
        statement = select(aion_mcp_capability_mappings)
        if mcp_server_id is not None:
            statement = statement.where(
                aion_mcp_capability_mappings.c.mcp_server_id == mcp_server_id
            )
        if status is not None:
            statement = statement.where(aion_mcp_capability_mappings.c.status == status)
        statement = statement.order_by(aion_mcp_capability_mappings.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_mapping_from_row(row) for row in rows]

    def record_sync(self, response: MCPSyncResponse) -> MCPSyncResponse:
        """Persist one MCP sync record."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_mcp_sync_records).values(
                    sync_id=response.sync_id,
                    mcp_server_id=response.mcp_server_id,
                    status=response.status,
                    discovered_tools=response.discovered_tools,
                    mapped_capabilities=response.mapped_capabilities,
                    skipped=response.skipped,
                    failed=response.failed,
                    errors=response.errors,
                    created_at=response.created_at,
                )
            )
        return response

    def record_invocation(self, result: MCPInvocationResult) -> MCPInvocationResult:
        """Persist one MCP invocation record."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_mcp_invocation_records).values(
                    mcp_invocation_id=result.mcp_invocation_id,
                    invocation_id=result.invocation_id,
                    mcp_server_id=result.mcp_server_id,
                    mcp_tool_name=result.mcp_tool_name,
                    capability_id=result.capability_id,
                    trace_id=None,
                    execution_id=None,
                    step_run_id=None,
                    status=result.status,
                    request={},
                    response=result.output,
                    error=result.error,
                    latency_ms=result.latency_ms,
                    policy_decision_id=result.policy_decision_id,
                    created_at=result.created_at,
                )
            )
        return result

    def update_server_health(
        self,
        server_id: str,
        health: MCPServerHealth,
    ) -> MCPServerRecord:
        """Persist server health metadata."""
        server = self.get_server(server_id)
        if server is None:
            raise KeyError(server_id)
        health_status = "healthy" if health.status == "healthy" else health.status
        if health_status == "unavailable":
            health_status = "unhealthy"
        updated = server.model_copy(
            update={
                "health_status": cast(MCPHealthStatus, health_status),
                "last_health_check_at": health.checked_at,
                "updated_at": datetime.now(UTC),
            }
        )
        return self.create_server(updated)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        mcp_metadata.create_all(self._engine)
        self._schema_ready = True


def _server_from_row(row: RowMapping) -> MCPServerRecord:
    return MCPServerRecord(
        mcp_server_id=str(row["mcp_server_id"]),
        server_name=str(row["server_name"]),
        transport_type=cast(MCPTransportType, str(row["transport_type"])),
        endpoint_ref=_optional_str(row["endpoint_ref"]),
        status=cast(MCPServerStatus, str(row["status"])),
        health_status=cast(MCPHealthStatus, str(row["health_status"])),
        config=_dict(row["config"]),
        owner_scope=list(row["owner_scope"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        last_health_check_at=_optional_datetime(row["last_health_check_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _mapping_from_row(row: RowMapping) -> MCPCapabilityMapping:
    return MCPCapabilityMapping(
        mapping_id=str(row["mapping_id"]),
        mcp_server_id=str(row["mcp_server_id"]),
        mcp_tool_name=str(row["mcp_tool_name"]),
        capability_id=str(row["capability_id"]),
        module_id=str(row["module_id"]),
        risk_level=cast(MCPRiskLevel, str(row["risk_level"])),
        status=cast(MCPMappingStatus, str(row["status"])),
        input_schema=_dict(row["input_schema"]),
        output_schema=_dict(row["output_schema"]),
        permissions_required=list(row["permissions_required"]),
        memory_read_scopes=list(row["memory_read_scopes"]),
        memory_write_scopes=list(row["memory_write_scopes"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
