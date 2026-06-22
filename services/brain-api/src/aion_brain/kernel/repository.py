"""Persistent kernel lifecycle repository with a local read-through cache."""

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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.kernel import (
    KernelAdapterConfig,
    KernelBootRecord,
    KernelBootStatus,
    KernelSelfTestResult,
    KernelSelfTestStatus,
    KernelServiceRecord,
    KernelServiceStatus,
    KernelServiceType,
)

kernel_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_kernel_boot_records = Table(
    "aion_kernel_boot_records",
    kernel_metadata,
    Column("boot_id", Text, primary_key=True),
    Column("service_name", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("env", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("adapter_config", json_payload_type, nullable=False),
    Column("diagnostics", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_kernel_boot_records_service_name", "service_name"),
    Index("ix_aion_kernel_boot_records_version", "version"),
    Index("ix_aion_kernel_boot_records_env", "env"),
    Index("ix_aion_kernel_boot_records_status", "status"),
    Index("ix_aion_kernel_boot_records_started_at", "started_at"),
)

aion_kernel_service_records = Table(
    "aion_kernel_service_records",
    kernel_metadata,
    Column("service_record_id", Text, primary_key=True),
    Column("service_name", Text, nullable=False),
    Column("service_type", Text, nullable=False),
    Column("adapter_name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("health", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_kernel_service_records_service_name", "service_name"),
    Index("ix_aion_kernel_service_records_service_type", "service_type"),
    Index("ix_aion_kernel_service_records_adapter_name", "adapter_name"),
    Index("ix_aion_kernel_service_records_status", "status"),
    Index("ix_aion_kernel_service_records_created_at", "created_at"),
)

aion_kernel_self_test_runs = Table(
    "aion_kernel_self_test_runs",
    kernel_metadata,
    Column("self_test_id", Text, primary_key=True),
    Column("status", Text, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_kernel_self_test_runs_status", "status"),
    Index("ix_aion_kernel_self_test_runs_created_at", "created_at"),
)


class KernelRepository:
    """Store kernel lifecycle records while remaining safe before infrastructure is ready."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
        best_effort: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        self._engine = engine
        self._auto_create = auto_create
        self._best_effort = best_effort
        self._schema_ready = False
        self._boots: dict[str, KernelBootRecord] = {}
        self._services: dict[str, KernelServiceRecord] = {}
        self._self_tests: dict[str, KernelSelfTestResult] = {}

    def save_boot(self, record: KernelBootRecord) -> KernelBootRecord:
        """Persist a boot record."""
        self._boots[record.boot_id] = record
        self._write(
            aion_kernel_boot_records,
            "boot_id",
            record.boot_id,
            record.model_dump(mode="python"),
        )
        return record

    def get_latest_boot(self) -> KernelBootRecord | None:
        """Return the most recent boot record."""
        if self._boots:
            return max(
                self._boots.values(),
                key=lambda item: item.started_at or datetime.min.replace(tzinfo=UTC),
            )
        row = self._read_latest(aion_kernel_boot_records, "started_at")
        return _row_to_boot(row) if row is not None else None

    def save_service(self, record: KernelServiceRecord) -> KernelServiceRecord:
        """Persist a service registry record."""
        self._services[record.service_record_id] = record
        self._write(
            aion_kernel_service_records,
            "service_record_id",
            record.service_record_id,
            record.model_dump(mode="python"),
        )
        return record

    def list_services(self) -> list[KernelServiceRecord]:
        """Return registered services."""
        if self._services:
            return sorted(self._services.values(), key=lambda item: item.service_name)
        rows = self._read_all(aion_kernel_service_records, "service_name")
        return [_row_to_service(row) for row in rows]

    def save_self_test(self, result: KernelSelfTestResult) -> KernelSelfTestResult:
        """Persist a self-test result."""
        self._self_tests[result.self_test_id] = result
        values = result.model_dump(mode="python")
        values["checks"] = [check.model_dump(mode="json") for check in result.checks]
        self._write(aion_kernel_self_test_runs, "self_test_id", result.self_test_id, values)
        return result

    def get_latest_self_test(self) -> KernelSelfTestResult | None:
        """Return the latest self-test result."""
        if self._self_tests:
            return max(self._self_tests.values(), key=lambda item: item.created_at)
        row = self._read_latest(aion_kernel_self_test_runs, "created_at")
        return _row_to_self_test(row) if row is not None else None

    def _write(self, table: Table, key: str, value: str, values: dict[str, Any]) -> None:
        try:
            self._ensure_schema()
            with self._engine.begin() as connection:
                connection.execute(delete(table).where(table.c[key] == value))
                connection.execute(insert(table).values(**values))
        except Exception:
            if not self._best_effort:
                raise

    def _read_latest(self, table: Table, order_column: str) -> RowMapping | None:
        try:
            self._ensure_schema()
            statement = select(table).order_by(table.c[order_column].desc()).limit(1)
            with self._engine.connect() as connection:
                return connection.execute(statement).mappings().first()
        except Exception:
            if not self._best_effort:
                raise
            return None

    def _read_all(self, table: Table, order_column: str) -> list[RowMapping]:
        try:
            self._ensure_schema()
            with self._engine.connect() as connection:
                rows = connection.execute(select(table).order_by(table.c[order_column]))
                return list(rows.mappings())
        except Exception:
            if not self._best_effort:
                raise
            return []

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        kernel_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_boot(row: RowMapping) -> KernelBootRecord:
    return KernelBootRecord(
        boot_id=str(row["boot_id"]),
        service_name=str(row["service_name"]),
        version=str(row["version"]),
        env=str(row["env"]),
        status=cast(KernelBootStatus, str(row["status"])),
        adapter_config=KernelAdapterConfig.model_validate(row["adapter_config"]),
        diagnostics=dict(row["diagnostics"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_service(row: RowMapping) -> KernelServiceRecord:
    return KernelServiceRecord(
        service_record_id=str(row["service_record_id"]),
        service_name=str(row["service_name"]),
        service_type=cast(KernelServiceType, str(row["service_type"])),
        adapter_name=str(row["adapter_name"]),
        status=cast(KernelServiceStatus, str(row["status"])),
        health=dict(row["health"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _row_to_self_test(row: RowMapping) -> KernelSelfTestResult:
    return KernelSelfTestResult(
        self_test_id=str(row["self_test_id"]),
        status=cast(KernelSelfTestStatus, str(row["status"])),
        checks=list(row["checks"]),
        report=dict(row["report"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError("Expected datetime-compatible value")


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)
