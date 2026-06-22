"""Persistence for runtime configuration control-plane records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
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

from aion_brain.contracts.runtime_config import (
    ConfigChangeRecord,
    ConfigProfile,
    ConfigSnapshot,
    ConfigValidationRun,
    FeatureFlagOverride,
    RuntimeConfigValue,
)

runtime_config_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")
ModelT = TypeVar(
    "ModelT",
    ConfigProfile,
    RuntimeConfigValue,
    FeatureFlagOverride,
    ConfigSnapshot,
    ConfigValidationRun,
    ConfigChangeRecord,
)

aion_config_profiles = Table(
    "aion_config_profiles",
    runtime_config_metadata,
    Column("config_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("profile_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("values", json_payload_type, nullable=False),
    Column("feature_flags", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("name", name="uq_aion_config_profiles_name"),
    Index("ix_aion_config_profiles_name", "name"),
    Index("ix_aion_config_profiles_status", "status"),
    Index("ix_aion_config_profiles_profile_type", "profile_type"),
    Index("ix_aion_config_profiles_created_at", "created_at"),
)

aion_config_values = Table(
    "aion_config_values",
    runtime_config_metadata,
    Column("config_value_id", Text, primary_key=True),
    Column("config_key", Text, nullable=False),
    Column("config_value", json_payload_type, nullable=False),
    Column("value_type", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("sensitive", Boolean, nullable=False),
    Column("mutable", Boolean, nullable=False),
    Column("requires_restart", Boolean, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("config_key", "source", name="uq_aion_config_values_key_source"),
    Index("ix_aion_config_values_config_key", "config_key"),
    Index("ix_aion_config_values_value_type", "value_type"),
    Index("ix_aion_config_values_source", "source"),
    Index("ix_aion_config_values_status", "status"),
    Index("ix_aion_config_values_sensitive", "sensitive"),
    Index("ix_aion_config_values_mutable", "mutable"),
    Index("ix_aion_config_values_requires_restart", "requires_restart"),
    Index("ix_aion_config_values_created_at", "created_at"),
)

aion_feature_flag_overrides = Table(
    "aion_feature_flag_overrides",
    runtime_config_metadata,
    Column("feature_override_id", Text, primary_key=True),
    Column("feature_key", Text, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("source", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_feature_flag_overrides_feature_key", "feature_key"),
    Index("ix_aion_feature_flag_overrides_enabled", "enabled"),
    Index("ix_aion_feature_flag_overrides_source", "source"),
    Index("ix_aion_feature_flag_overrides_status", "status"),
    Index("ix_aion_feature_flag_overrides_actor_id", "actor_id"),
    Index("ix_aion_feature_flag_overrides_workspace_id", "workspace_id"),
    Index("ix_aion_feature_flag_overrides_expires_at", "expires_at"),
    Index("ix_aion_feature_flag_overrides_created_at", "created_at"),
)

aion_config_snapshots = Table(
    "aion_config_snapshots",
    runtime_config_metadata,
    Column("config_snapshot_id", Text, primary_key=True),
    Column("snapshot_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("settings", json_payload_type, nullable=False),
    Column("feature_flags", json_payload_type, nullable=False),
    Column("adapter_status", json_payload_type, nullable=False),
    Column("config_hash", Text, nullable=False),
    Column("drift_from_snapshot_id", Text, nullable=True),
    Column("drift", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_config_snapshots_snapshot_type", "snapshot_type"),
    Index("ix_aion_config_snapshots_status", "status"),
    Index("ix_aion_config_snapshots_config_hash", "config_hash"),
    Index("ix_aion_config_snapshots_drift_from_snapshot_id", "drift_from_snapshot_id"),
    Index("ix_aion_config_snapshots_created_at", "created_at"),
)

aion_config_validation_runs = Table(
    "aion_config_validation_runs",
    runtime_config_metadata,
    Column("config_validation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("profile_id", Text, nullable=True),
    Column("snapshot_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_config_validation_runs_trace_id", "trace_id"),
    Index("ix_aion_config_validation_runs_profile_id", "profile_id"),
    Index("ix_aion_config_validation_runs_snapshot_id", "snapshot_id"),
    Index("ix_aion_config_validation_runs_status", "status"),
    Index("ix_aion_config_validation_runs_created_at", "created_at"),
)

aion_config_change_records = Table(
    "aion_config_change_records",
    runtime_config_metadata,
    Column("config_change_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("change_type", Text, nullable=False),
    Column("before", json_payload_type, nullable=False),
    Column("after", json_payload_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_config_change_records_trace_id", "trace_id"),
    Index("ix_aion_config_change_records_actor_id", "actor_id"),
    Index("ix_aion_config_change_records_workspace_id", "workspace_id"),
    Index("ix_aion_config_change_records_target_type", "target_type"),
    Index("ix_aion_config_change_records_target_id", "target_id"),
    Index("ix_aion_config_change_records_change_type", "change_type"),
    Index("ix_aion_config_change_records_created_at", "created_at"),
)


class RuntimeConfigRepository:
    """Store local runtime configuration records."""

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

    def save_profile(self, record: ConfigProfile) -> ConfigProfile:
        return self._replace(
            aion_config_profiles,
            "config_profile_id",
            record,
            ConfigProfile,
            timestamp_fields=("created_at", "updated_at"),
        )

    def get_profile(self, config_profile_id: str) -> ConfigProfile | None:
        row = self._get(aion_config_profiles, "config_profile_id", config_profile_id)
        return ConfigProfile(**dict(row)) if row else None

    def list_profiles(
        self,
        *,
        status: str | None = None,
        profile_type: str | None = None,
    ) -> list[ConfigProfile]:
        statement = select(aion_config_profiles).order_by(aion_config_profiles.c.created_at.desc())
        if status:
            statement = statement.where(aion_config_profiles.c.status == status)
        if profile_type:
            statement = statement.where(aion_config_profiles.c.profile_type == profile_type)
        return [ConfigProfile(**dict(row)) for row in self._list(statement)]

    def active_profile(self) -> ConfigProfile | None:
        statement = (
            select(aion_config_profiles)
            .where(aion_config_profiles.c.status == "active")
            .order_by(aion_config_profiles.c.updated_at.desc())
        )
        rows = self._list(statement)
        return ConfigProfile(**dict(rows[0])) if rows else None

    def save_value(self, record: RuntimeConfigValue) -> RuntimeConfigValue:
        return self._replace(
            aion_config_values,
            "config_value_id",
            record,
            RuntimeConfigValue,
            timestamp_fields=("created_at", "updated_at"),
        )

    def get_value(self, config_value_id: str) -> RuntimeConfigValue | None:
        row = self._get(aion_config_values, "config_value_id", config_value_id)
        return RuntimeConfigValue(**dict(row)) if row else None

    def save_override(self, record: FeatureFlagOverride) -> FeatureFlagOverride:
        return self._replace(
            aion_feature_flag_overrides,
            "feature_override_id",
            record,
            FeatureFlagOverride,
            timestamp_fields=("created_at",),
        )

    def get_override(self, feature_override_id: str) -> FeatureFlagOverride | None:
        row = self._get(aion_feature_flag_overrides, "feature_override_id", feature_override_id)
        return FeatureFlagOverride(**dict(row)) if row else None

    def list_overrides(
        self,
        *,
        feature_key: str | None = None,
        status: str | None = None,
    ) -> list[FeatureFlagOverride]:
        statement = select(aion_feature_flag_overrides).order_by(
            aion_feature_flag_overrides.c.created_at.desc()
        )
        if feature_key:
            statement = statement.where(aion_feature_flag_overrides.c.feature_key == feature_key)
        if status:
            statement = statement.where(aion_feature_flag_overrides.c.status == status)
        return [FeatureFlagOverride(**dict(row)) for row in self._list(statement)]

    def save_snapshot(self, record: ConfigSnapshot) -> ConfigSnapshot:
        return self._replace(
            aion_config_snapshots,
            "config_snapshot_id",
            record,
            ConfigSnapshot,
            timestamp_fields=("created_at",),
        )

    def get_snapshot(self, config_snapshot_id: str) -> ConfigSnapshot | None:
        row = self._get(aion_config_snapshots, "config_snapshot_id", config_snapshot_id)
        return ConfigSnapshot(**dict(row)) if row else None

    def list_snapshots(
        self,
        *,
        snapshot_type: str | None = None,
        limit: int = 50,
    ) -> list[ConfigSnapshot]:
        statement = select(aion_config_snapshots).order_by(
            aion_config_snapshots.c.created_at.desc()
        )
        if snapshot_type:
            statement = statement.where(aion_config_snapshots.c.snapshot_type == snapshot_type)
        statement = statement.limit(limit)
        return [ConfigSnapshot(**dict(row)) for row in self._list(statement)]

    def latest_snapshot(self) -> ConfigSnapshot | None:
        snapshots = self.list_snapshots(limit=1)
        return snapshots[0] if snapshots else None

    def save_validation_run(self, record: ConfigValidationRun) -> ConfigValidationRun:
        return self._replace(
            aion_config_validation_runs,
            "config_validation_id",
            record,
            ConfigValidationRun,
            timestamp_fields=("created_at",),
        )

    def get_validation_run(self, config_validation_id: str) -> ConfigValidationRun | None:
        row = self._get(
            aion_config_validation_runs,
            "config_validation_id",
            config_validation_id,
        )
        return ConfigValidationRun(**dict(row)) if row else None

    def latest_validation_run(self) -> ConfigValidationRun | None:
        statement = select(aion_config_validation_runs).order_by(
            aion_config_validation_runs.c.created_at.desc()
        )
        rows = self._list(statement.limit(1))
        return ConfigValidationRun(**dict(rows[0])) if rows else None

    def save_change(self, record: ConfigChangeRecord) -> ConfigChangeRecord:
        return self._replace(
            aion_config_change_records,
            "config_change_id",
            record,
            ConfigChangeRecord,
            timestamp_fields=("created_at",),
        )

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
        excluded = set(timestamp_fields)
        values = record.model_dump(mode="python", exclude=excluded)
        for field in timestamp_fields:
            values[field] = getattr(record, field) or now
        with self._engine.begin() as connection:
            connection.execute(delete(table).where(table.c[id_column] == values[id_column]))
            connection.execute(insert(table).values(**values))
        return model(**values)

    def _get(self, table: Table, id_column: str, value: str) -> RowMapping | None:
        self._ensure_schema()
        statement = select(table).where(table.c[id_column] == value)
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _list(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())

    def _ensure_schema(self) -> None:
        if not self._schema_ready and self._auto_create:
            runtime_config_metadata.create_all(self._engine)
            self._schema_ready = True
