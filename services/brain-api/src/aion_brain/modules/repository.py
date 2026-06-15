"""Persistent module runtime repository."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
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

from aion_brain.contracts.modules import (
    CapabilityRuntimeBinding,
    CapabilityRuntimeBindingStatus,
    InvocationMode,
    ModuleHealthCheck,
    ModuleHealthStatus,
    ModuleRuntime,
    ModuleRuntimeStatus,
    RuntimeType,
)

module_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_module_runtimes = Table(
    "aion_module_runtimes",
    module_metadata,
    Column("runtime_id", Text, primary_key=True),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("runtime_type", Text, nullable=False),
    Column("endpoint_ref", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("health_status", Text, nullable=False),
    Column("config", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_health_check_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_runtimes_module_id", "module_id"),
    Index("ix_aion_module_runtimes_version", "version"),
    Index("ix_aion_module_runtimes_runtime_type", "runtime_type"),
    Index("ix_aion_module_runtimes_status", "status"),
    Index("ix_aion_module_runtimes_health_status", "health_status"),
    Index("ix_aion_module_runtimes_created_at", "created_at"),
)

aion_capability_runtime_bindings = Table(
    "aion_capability_runtime_bindings",
    module_metadata,
    Column("binding_id", Text, primary_key=True),
    Column("capability_id", Text, nullable=False),
    Column("module_id", Text, nullable=False),
    Column("runtime_id", Text, nullable=False),
    Column("invocation_mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_capability_runtime_bindings_capability_id", "capability_id"),
    Index("ix_aion_capability_runtime_bindings_module_id", "module_id"),
    Index("ix_aion_capability_runtime_bindings_runtime_id", "runtime_id"),
    Index("ix_aion_capability_runtime_bindings_invocation_mode", "invocation_mode"),
    Index("ix_aion_capability_runtime_bindings_status", "status"),
    Index("ix_aion_capability_runtime_bindings_created_at", "created_at"),
)

aion_module_health_checks = Table(
    "aion_module_health_checks",
    module_metadata,
    Column("health_check_id", Text, primary_key=True),
    Column("runtime_id", Text, nullable=False),
    Column("module_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("details", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_module_health_checks_runtime_id", "runtime_id"),
    Index("ix_aion_module_health_checks_module_id", "module_id"),
    Index("ix_aion_module_health_checks_status", "status"),
    Index("ix_aion_module_health_checks_created_at", "created_at"),
)


class ModuleRuntimeRepository:
    """Repository for module runtimes, bindings, and health checks."""

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

    def save_runtime(self, runtime: ModuleRuntime) -> ModuleRuntime:
        """Upsert a module runtime."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = runtime.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = runtime.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_module_runtimes.c.runtime_id).where(
                    aion_module_runtimes.c.runtime_id == runtime.runtime_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_module_runtimes).values(**values))
            else:
                connection.execute(
                    update(aion_module_runtimes)
                    .where(aion_module_runtimes.c.runtime_id == runtime.runtime_id)
                    .values(**values)
                )
        return stored

    def get_runtime(self, runtime_id: str) -> ModuleRuntime | None:
        """Return a module runtime by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_module_runtimes).where(
                    aion_module_runtimes.c.runtime_id == runtime_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_runtime(row)

    def list_runtimes(self) -> list[ModuleRuntime]:
        """Return all registered runtimes."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(aion_module_runtimes).order_by(aion_module_runtimes.c.created_at)
            ).mappings().all()
        return [_row_to_runtime(row) for row in rows]

    def save_binding(self, binding: CapabilityRuntimeBinding) -> CapabilityRuntimeBinding:
        """Upsert a capability runtime binding."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = binding.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = binding.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_capability_runtime_bindings.c.binding_id).where(
                    aion_capability_runtime_bindings.c.binding_id == binding.binding_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_capability_runtime_bindings).values(**values))
            else:
                connection.execute(
                    update(aion_capability_runtime_bindings)
                    .where(
                        aion_capability_runtime_bindings.c.binding_id == binding.binding_id
                    )
                    .values(**values)
                )
        return stored

    def get_binding(self, binding_id: str) -> CapabilityRuntimeBinding | None:
        """Return a capability runtime binding by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_capability_runtime_bindings).where(
                    aion_capability_runtime_bindings.c.binding_id == binding_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_binding(row)

    def get_active_binding(
        self,
        capability_id: str,
        invocation_mode: str,
    ) -> CapabilityRuntimeBinding | None:
        """Return the active binding for a capability and invocation mode."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_capability_runtime_bindings)
                .where(aion_capability_runtime_bindings.c.capability_id == capability_id)
                .where(aion_capability_runtime_bindings.c.invocation_mode == invocation_mode)
                .where(aion_capability_runtime_bindings.c.status == "active")
                .order_by(aion_capability_runtime_bindings.c.created_at.desc())
            ).mappings().first()
        if row is None:
            return None
        return _row_to_binding(row)

    def list_bindings(self) -> list[CapabilityRuntimeBinding]:
        """Return all capability runtime bindings."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(aion_capability_runtime_bindings).order_by(
                    aion_capability_runtime_bindings.c.created_at
                )
            ).mappings().all()
        return [_row_to_binding(row) for row in rows]

    def save_health_check(self, health_check: ModuleHealthCheck) -> ModuleHealthCheck:
        """Persist a runtime health check."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_module_health_checks).values(
                    **health_check.model_dump(mode="python")
                )
            )
        return health_check

    def update_runtime_health(
        self,
        runtime_id: str,
        health_status: str,
        checked_at: datetime,
    ) -> ModuleRuntime | None:
        """Update runtime health status and return the updated runtime."""
        runtime = self.get_runtime(runtime_id)
        if runtime is None:
            return None
        updated = runtime.model_copy(
            update={"health_status": health_status, "last_health_check_at": checked_at}
        )
        return self.save_runtime(updated)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        module_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_runtime(row: RowMapping) -> ModuleRuntime:
    return ModuleRuntime(
        runtime_id=str(row["runtime_id"]),
        module_id=str(row["module_id"]),
        version=str(row["version"]),
        runtime_type=cast(RuntimeType, str(row["runtime_type"])),
        endpoint_ref=_optional_str(row["endpoint_ref"]),
        status=cast(ModuleRuntimeStatus, str(row["status"])),
        health_status=cast(ModuleHealthStatus, str(row["health_status"])),
        config=_dict(row["config"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        last_health_check_at=_optional_datetime(row["last_health_check_at"]),
    )


def _row_to_binding(row: RowMapping) -> CapabilityRuntimeBinding:
    return CapabilityRuntimeBinding(
        binding_id=str(row["binding_id"]),
        capability_id=str(row["capability_id"]),
        module_id=str(row["module_id"]),
        runtime_id=str(row["runtime_id"]),
        invocation_mode=cast(InvocationMode, str(row["invocation_mode"])),
        status=cast(CapabilityRuntimeBindingStatus, str(row["status"])),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}
