"""Persistence for resilience control-plane records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.resilience import (
    CircuitBreaker,
    DegradedModeEvent,
    DependencyHealth,
    FaultInjectionRule,
    ResilienceTestRun,
    RetryPolicy,
)

resilience_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")
ModelT = TypeVar(
    "ModelT",
    DependencyHealth,
    RetryPolicy,
    CircuitBreaker,
    DegradedModeEvent,
    FaultInjectionRule,
    ResilienceTestRun,
)

aion_dependency_health_records = Table(
    "aion_dependency_health_records",
    resilience_metadata,
    Column("dependency_health_id", Text, primary_key=True),
    Column("dependency_name", Text, nullable=False),
    Column("dependency_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("criticality", Text, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("details", json_payload_type, nullable=False),
    Column("checked_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_dependency_health_name", "dependency_name"),
    Index("ix_aion_dependency_health_type", "dependency_type"),
    Index("ix_aion_dependency_health_status", "status"),
    Index("ix_aion_dependency_health_criticality", "criticality"),
    Index("ix_aion_dependency_health_checked_at", "checked_at"),
)

aion_retry_policies = Table(
    "aion_retry_policies",
    resilience_metadata,
    Column("retry_policy_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("max_attempts", Integer, nullable=False),
    Column("initial_delay_ms", Integer, nullable=False),
    Column("max_delay_ms", Integer, nullable=False),
    Column("backoff_multiplier", Float, nullable=False),
    Column("jitter_enabled", Boolean, nullable=False),
    Column("retryable_statuses", json_payload_type, nullable=False),
    Column("non_retryable_statuses", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("name", name="uq_aion_retry_policies_name"),
    Index("ix_aion_retry_policies_name", "name"),
    Index("ix_aion_retry_policies_status", "status"),
    Index("ix_aion_retry_policies_target_type", "target_type"),
    Index("ix_aion_retry_policies_created_at", "created_at"),
)

aion_circuit_breakers = Table(
    "aion_circuit_breakers",
    resilience_metadata,
    Column("circuit_breaker_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("failure_count", Integer, nullable=False),
    Column("success_count", Integer, nullable=False),
    Column("failure_threshold", Integer, nullable=False),
    Column("recovery_timeout_seconds", Integer, nullable=False),
    Column("half_open_max_calls", Integer, nullable=False),
    Column("last_failure_at", DateTime(timezone=True), nullable=True),
    Column("opened_at", DateTime(timezone=True), nullable=True),
    Column("half_opened_at", DateTime(timezone=True), nullable=True),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("name", name="uq_aion_circuit_breakers_name"),
    Index("ix_aion_circuit_breakers_name", "name"),
    Index("ix_aion_circuit_breakers_target_type", "target_type"),
    Index("ix_aion_circuit_breakers_target_id", "target_id"),
    Index("ix_aion_circuit_breakers_status", "status"),
    Index("ix_aion_circuit_breakers_opened_at", "opened_at"),
    Index("ix_aion_circuit_breakers_created_at", "created_at"),
)

aion_degraded_mode_events = Table(
    "aion_degraded_mode_events",
    resilience_metadata,
    Column("degraded_event_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("component", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("dependencies", json_payload_type, nullable=False),
    Column("fallbacks_active", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_degraded_mode_trace_id", "trace_id"),
    Index("ix_aion_degraded_mode_component", "component"),
    Index("ix_aion_degraded_mode_status", "status"),
    Index("ix_aion_degraded_mode_severity", "severity"),
    Index("ix_aion_degraded_mode_created_at", "created_at"),
    Index("ix_aion_degraded_mode_resolved_at", "resolved_at"),
)

aion_fault_injection_rules = Table(
    "aion_fault_injection_rules",
    resilience_metadata,
    Column("fault_rule_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("fault_type", Text, nullable=False),
    Column("probability", Float, nullable=False),
    Column("duration_ms", Integer, nullable=True),
    Column("error_code", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_fault_rules_name", "name"),
    Index("ix_aion_fault_rules_status", "status"),
    Index("ix_aion_fault_rules_target_type", "target_type"),
    Index("ix_aion_fault_rules_target_id", "target_id"),
    Index("ix_aion_fault_rules_fault_type", "fault_type"),
    Index("ix_aion_fault_rules_created_at", "created_at"),
)

aion_resilience_test_runs = Table(
    "aion_resilience_test_runs",
    resilience_metadata,
    Column("resilience_test_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("fault_rule_ids", json_payload_type, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_resilience_runs_trace_id", "trace_id"),
    Index("ix_aion_resilience_runs_status", "status"),
    Index("ix_aion_resilience_runs_mode", "mode"),
    Index("ix_aion_resilience_runs_created_at", "created_at"),
)


class ResilienceRepository:
    """Store local resilience control-plane records."""

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
            if database_url.startswith("sqlite") and ":memory:" in database_url:
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_dependency_health(self, record: DependencyHealth) -> DependencyHealth:
        return self._replace(
            aion_dependency_health_records,
            "dependency_health_id",
            record,
            DependencyHealth,
            timestamp_fields=("checked_at",),
        )

    def latest_dependency_health(self) -> list[DependencyHealth]:
        rows = self._list(
            select(aion_dependency_health_records).order_by(
                aion_dependency_health_records.c.checked_at.desc()
            )
        )
        latest: dict[str, DependencyHealth] = {}
        for row in rows:
            record = DependencyHealth(**dict(row))
            latest.setdefault(record.dependency_name, record)
        return list(latest.values())

    def save_retry_policy(self, record: RetryPolicy) -> RetryPolicy:
        return self._replace(
            aion_retry_policies,
            "retry_policy_id",
            record,
            RetryPolicy,
            timestamp_fields=("created_at", "updated_at"),
        )

    def get_retry_policy(self, name: str) -> RetryPolicy | None:
        row = self._first(select(aion_retry_policies).where(aion_retry_policies.c.name == name))
        return RetryPolicy(**dict(row)) if row else None

    def list_retry_policies(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[RetryPolicy]:
        statement = select(aion_retry_policies).order_by(aion_retry_policies.c.created_at.desc())
        if status:
            statement = statement.where(aion_retry_policies.c.status == status)
        if target_type:
            statement = statement.where(aion_retry_policies.c.target_type == target_type)
        return [RetryPolicy(**dict(row)) for row in self._list(statement)]

    def save_circuit_breaker(self, record: CircuitBreaker) -> CircuitBreaker:
        return self._replace(
            aion_circuit_breakers,
            "circuit_breaker_id",
            record,
            CircuitBreaker,
            timestamp_fields=("created_at", "updated_at"),
        )

    def get_circuit_breaker(self, name: str) -> CircuitBreaker | None:
        row = self._first(select(aion_circuit_breakers).where(aion_circuit_breakers.c.name == name))
        return CircuitBreaker(**dict(row)) if row else None

    def list_circuit_breakers(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[CircuitBreaker]:
        statement = select(aion_circuit_breakers).order_by(
            aion_circuit_breakers.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_circuit_breakers.c.status == status)
        if target_type:
            statement = statement.where(aion_circuit_breakers.c.target_type == target_type)
        return [CircuitBreaker(**dict(row)) for row in self._list(statement)]

    def save_degraded_event(self, record: DegradedModeEvent) -> DegradedModeEvent:
        return self._replace(
            aion_degraded_mode_events,
            "degraded_event_id",
            record,
            DegradedModeEvent,
            timestamp_fields=("created_at",),
        )

    def get_degraded_event(self, degraded_event_id: str) -> DegradedModeEvent | None:
        row = self._first(
            select(aion_degraded_mode_events).where(
                aion_degraded_mode_events.c.degraded_event_id == degraded_event_id
            )
        )
        return DegradedModeEvent(**dict(row)) if row else None

    def list_degraded_events(
        self,
        *,
        status: str | None = None,
        component: str | None = None,
    ) -> list[DegradedModeEvent]:
        statement = select(aion_degraded_mode_events).order_by(
            aion_degraded_mode_events.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_degraded_mode_events.c.status == status)
        if component:
            statement = statement.where(aion_degraded_mode_events.c.component == component)
        return [DegradedModeEvent(**dict(row)) for row in self._list(statement)]

    def save_fault_rule(self, record: FaultInjectionRule) -> FaultInjectionRule:
        return self._replace(
            aion_fault_injection_rules,
            "fault_rule_id",
            record,
            FaultInjectionRule,
            timestamp_fields=("created_at", "updated_at"),
        )

    def get_fault_rule(self, fault_rule_id: str) -> FaultInjectionRule | None:
        row = self._first(
            select(aion_fault_injection_rules).where(
                aion_fault_injection_rules.c.fault_rule_id == fault_rule_id
            )
        )
        return FaultInjectionRule(**dict(row)) if row else None

    def list_fault_rules(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[FaultInjectionRule]:
        statement = select(aion_fault_injection_rules).order_by(
            aion_fault_injection_rules.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_fault_injection_rules.c.status == status)
        if target_type:
            statement = statement.where(aion_fault_injection_rules.c.target_type == target_type)
        return [FaultInjectionRule(**dict(row)) for row in self._list(statement)]

    def save_test_run(self, record: ResilienceTestRun) -> ResilienceTestRun:
        return self._replace(
            aion_resilience_test_runs,
            "resilience_test_run_id",
            record,
            ResilienceTestRun,
            timestamp_fields=("created_at",),
        )

    def get_test_run(self, resilience_test_run_id: str) -> ResilienceTestRun | None:
        row = self._first(
            select(aion_resilience_test_runs).where(
                aion_resilience_test_runs.c.resilience_test_run_id == resilience_test_run_id
            )
        )
        return ResilienceTestRun(**dict(row)) if row else None

    def _replace(
        self,
        table: Table,
        id_column: str,
        record: ModelT,
        model: type[ModelT],
        *,
        timestamp_fields: tuple[str, ...],
    ) -> ModelT:
        self._ensure_schema()
        now = datetime.now(UTC)
        values = record.model_dump(mode="python", exclude=set(timestamp_fields))
        for field in timestamp_fields:
            values[field] = getattr(record, field) or now
        with self._engine.begin() as connection:
            connection.execute(delete(table).where(table.c[id_column] == values[id_column]))
            connection.execute(insert(table).values(**values))
        return model(**values)

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _list(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())

    def _ensure_schema(self) -> None:
        if not self._schema_ready and self._auto_create:
            resilience_metadata.create_all(self._engine)
            self._schema_ready = True
