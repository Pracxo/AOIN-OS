"""Persistence for versioning, compatibility, artifacts, and freeze gates."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.compatibility import (
    CompatibilityMatrix,
    CompatibilityStatus,
    MigrationBaseline,
    MigrationBaselineStatus,
    ReleaseArtifactManifest,
    ReleaseArtifactStatus,
)
from aion_brain.contracts.freeze import (
    FreezeGateCheck,
    FreezeGateRun,
    FreezeGateRunStatus,
)
from aion_brain.contracts.versioning import (
    FeatureCategory,
    FeatureRegistryEntry,
    FeatureStatus,
    ReleaseChannel,
    VersionManifest,
    VersionManifestStatus,
)

versioning_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_version_manifests = Table(
    "aion_version_manifests",
    versioning_metadata,
    Column("version_manifest_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("release_channel", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("api_version", Text, nullable=False),
    Column("sdk_version", Text, nullable=False),
    Column("schema_version", Text, nullable=False),
    Column("contract_hash", Text, nullable=False),
    Column("feature_flags", json_payload_type, nullable=False),
    Column("adapter_matrix", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_version_manifests_version", "version"),
    Index("ix_aion_version_manifests_release_channel", "release_channel"),
    Index("ix_aion_version_manifests_status", "status"),
    Index("ix_aion_version_manifests_api_version", "api_version"),
    Index("ix_aion_version_manifests_sdk_version", "sdk_version"),
    Index("ix_aion_version_manifests_schema_version", "schema_version"),
    Index("ix_aion_version_manifests_contract_hash", "contract_hash"),
    Index("ix_aion_version_manifests_created_at", "created_at"),
)

aion_feature_registry = Table(
    "aion_feature_registry",
    versioning_metadata,
    Column("feature_id", Text, primary_key=True),
    Column("feature_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("default_enabled", Boolean, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("dependencies", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deprecated_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("feature_key", name="uq_aion_feature_registry_feature_key"),
    Index("ix_aion_feature_registry_feature_key", "feature_key"),
    Index("ix_aion_feature_registry_status", "status"),
    Index("ix_aion_feature_registry_category", "category"),
    Index("ix_aion_feature_registry_default_enabled", "default_enabled"),
    Index("ix_aion_feature_registry_required", "required"),
    Index("ix_aion_feature_registry_created_at", "created_at"),
)

aion_compatibility_matrix_records = Table(
    "aion_compatibility_matrix_records",
    versioning_metadata,
    Column("compatibility_matrix_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("api_version", Text, nullable=False),
    Column("sdk_version", Text, nullable=False),
    Column("python_version", Text, nullable=False),
    Column("docker_compose_version", Text, nullable=True),
    Column("postgres_version", Text, nullable=True),
    Column("redis_version", Text, nullable=True),
    Column("nats_version", Text, nullable=True),
    Column("opa_version", Text, nullable=True),
    Column("optional_adapters", json_payload_type, nullable=False),
    Column("compatibility", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_compatibility_matrix_records_version", "version"),
    Index("ix_aion_compatibility_matrix_records_api_version", "api_version"),
    Index("ix_aion_compatibility_matrix_records_sdk_version", "sdk_version"),
    Index("ix_aion_compatibility_matrix_records_python_version", "python_version"),
    Index("ix_aion_compatibility_matrix_records_status", "status"),
    Index("ix_aion_compatibility_matrix_records_created_at", "created_at"),
)

aion_migration_baseline_records = Table(
    "aion_migration_baseline_records",
    versioning_metadata,
    Column("migration_baseline_id", Text, primary_key=True),
    Column("schema_version", Text, nullable=False),
    Column("migration_count", Integer, nullable=False),
    Column("migration_hash", Text, nullable=False),
    Column("destructive_migrations", json_payload_type, nullable=False),
    Column("tables", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_migration_baseline_records_schema_version", "schema_version"),
    Index("ix_aion_migration_baseline_records_migration_hash", "migration_hash"),
    Index("ix_aion_migration_baseline_records_status", "status"),
    Index("ix_aion_migration_baseline_records_created_at", "created_at"),
)

aion_release_artifact_manifests = Table(
    "aion_release_artifact_manifests",
    versioning_metadata,
    Column("release_artifact_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("artifacts", json_payload_type, nullable=False),
    Column("checksums", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_release_artifact_manifests_version", "version"),
    Index("ix_aion_release_artifact_manifests_status", "status"),
    Index("ix_aion_release_artifact_manifests_created_at", "created_at"),
)

aion_freeze_gate_runs = Table(
    "aion_freeze_gate_runs",
    versioning_metadata,
    Column("freeze_gate_id", Text, primary_key=True),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("requested_by", Text, nullable=True),
    Column("checks", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_freeze_gate_runs_version", "version"),
    Index("ix_aion_freeze_gate_runs_status", "status"),
    Index("ix_aion_freeze_gate_runs_requested_by", "requested_by"),
    Index("ix_aion_freeze_gate_runs_created_at", "created_at"),
)


class VersioningRepository:
    """Store AION v0.1 release freeze-control records."""

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

    def save_manifest(self, manifest: VersionManifest) -> VersionManifest:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_version_manifests).where(
                    aion_version_manifests.c.version_manifest_id == manifest.version_manifest_id
                )
            )
            connection.execute(
                insert(aion_version_manifests).values(**manifest.model_dump(mode="python"))
            )
        return manifest

    def get_manifest(self, version: str) -> VersionManifest | None:
        self._ensure_schema()
        statement = (
            select(aion_version_manifests)
            .where(aion_version_manifests.c.version == version)
            .order_by(aion_version_manifests.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_manifest(row) if row is not None else None

    def list_manifests(self, status: str | None = None) -> list[VersionManifest]:
        self._ensure_schema()
        statement = select(aion_version_manifests)
        if status:
            statement = statement.where(aion_version_manifests.c.status == status)
        statement = statement.order_by(aion_version_manifests.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_manifest(row) for row in rows]

    def save_feature(self, entry: FeatureRegistryEntry) -> FeatureRegistryEntry:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_feature_registry).where(
                    aion_feature_registry.c.feature_key == entry.feature_key
                )
            )
            connection.execute(
                insert(aion_feature_registry).values(**entry.model_dump(mode="python"))
            )
        return entry

    def get_feature(self, feature_key: str) -> FeatureRegistryEntry | None:
        self._ensure_schema()
        statement = select(aion_feature_registry).where(
            aion_feature_registry.c.feature_key == feature_key
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_feature(row) if row is not None else None

    def list_features(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> list[FeatureRegistryEntry]:
        self._ensure_schema()
        statement = select(aion_feature_registry)
        if status:
            statement = statement.where(aion_feature_registry.c.status == status)
        if category:
            statement = statement.where(aion_feature_registry.c.category == category)
        statement = statement.order_by(aion_feature_registry.c.feature_key)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_feature(row) for row in rows]

    def save_compatibility(self, record: CompatibilityMatrix) -> CompatibilityMatrix:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_compatibility_matrix_records).where(
                    aion_compatibility_matrix_records.c.compatibility_matrix_id
                    == record.compatibility_matrix_id
                )
            )
            connection.execute(
                insert(aion_compatibility_matrix_records).values(**record.model_dump(mode="python"))
            )
        return record

    def get_compatibility(self, version: str) -> CompatibilityMatrix | None:
        self._ensure_schema()
        statement = (
            select(aion_compatibility_matrix_records)
            .where(aion_compatibility_matrix_records.c.version == version)
            .order_by(aion_compatibility_matrix_records.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_compatibility(row) if row is not None else None

    def save_migration_baseline(self, record: MigrationBaseline) -> MigrationBaseline:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_migration_baseline_records).where(
                    aion_migration_baseline_records.c.migration_baseline_id
                    == record.migration_baseline_id
                )
            )
            connection.execute(
                insert(aion_migration_baseline_records).values(**record.model_dump(mode="python"))
            )
        return record

    def latest_migration_baseline(self, schema_version: str) -> MigrationBaseline | None:
        self._ensure_schema()
        statement = (
            select(aion_migration_baseline_records)
            .where(aion_migration_baseline_records.c.schema_version == schema_version)
            .order_by(aion_migration_baseline_records.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_migration_baseline(row) if row is not None else None

    def save_release_artifact(
        self,
        manifest: ReleaseArtifactManifest,
    ) -> ReleaseArtifactManifest:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_release_artifact_manifests).where(
                    aion_release_artifact_manifests.c.release_artifact_id
                    == manifest.release_artifact_id
                )
            )
            connection.execute(
                insert(aion_release_artifact_manifests).values(**manifest.model_dump(mode="python"))
            )
        return manifest

    def latest_release_artifact(self, version: str) -> ReleaseArtifactManifest | None:
        self._ensure_schema()
        statement = (
            select(aion_release_artifact_manifests)
            .where(aion_release_artifact_manifests.c.version == version)
            .order_by(aion_release_artifact_manifests.c.created_at.desc())
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_release_artifact(row) if row is not None else None

    def save_freeze_gate(self, run: FreezeGateRun) -> FreezeGateRun:
        self._ensure_schema()
        values = run.model_dump(mode="python", exclude={"checks"})
        values["checks"] = [check.model_dump(mode="json") for check in run.checks]
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_freeze_gate_runs).where(
                    aion_freeze_gate_runs.c.freeze_gate_id == run.freeze_gate_id
                )
            )
            connection.execute(insert(aion_freeze_gate_runs).values(**values))
        return run

    def get_freeze_gate(self, freeze_gate_id: str) -> FreezeGateRun | None:
        self._ensure_schema()
        statement = select(aion_freeze_gate_runs).where(
            aion_freeze_gate_runs.c.freeze_gate_id == freeze_gate_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_freeze_gate(row) if row is not None else None

    def list_freeze_gates(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[FreezeGateRun]:
        self._ensure_schema()
        statement = select(aion_freeze_gate_runs)
        if version:
            statement = statement.where(aion_freeze_gate_runs.c.version == version)
        if status:
            statement = statement.where(aion_freeze_gate_runs.c.status == status)
        statement = statement.order_by(aion_freeze_gate_runs.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_freeze_gate(row) for row in rows]

    def latest_passed_freeze_gate(self, version: str) -> FreezeGateRun | None:
        runs = self.list_freeze_gates(version=version, status="passed", limit=1)
        return runs[0] if runs else None

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        versioning_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_manifest(row: RowMapping) -> VersionManifest:
    return VersionManifest(
        version_manifest_id=str(row["version_manifest_id"]),
        version=str(row["version"]),
        release_channel=cast(ReleaseChannel, str(row["release_channel"])),
        status=cast(VersionManifestStatus, str(row["status"])),
        api_version=str(row["api_version"]),
        sdk_version=str(row["sdk_version"]),
        schema_version=str(row["schema_version"]),
        contract_hash=str(row["contract_hash"]),
        feature_flags=dict(row["feature_flags"]),
        adapter_matrix=dict(row["adapter_matrix"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_feature(row: RowMapping) -> FeatureRegistryEntry:
    return FeatureRegistryEntry(
        feature_id=str(row["feature_id"]),
        feature_key=str(row["feature_key"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(FeatureStatus, str(row["status"])),
        category=cast(FeatureCategory, str(row["category"])),
        default_enabled=bool(row["default_enabled"]),
        required=bool(row["required"]),
        owner_scope=_string_list(row["owner_scope"]),
        dependencies=_string_list(row["dependencies"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        deprecated_at=_optional_datetime(row["deprecated_at"]),
    )


def _row_to_compatibility(row: RowMapping) -> CompatibilityMatrix:
    return CompatibilityMatrix(
        compatibility_matrix_id=str(row["compatibility_matrix_id"]),
        version=str(row["version"]),
        api_version=str(row["api_version"]),
        sdk_version=str(row["sdk_version"]),
        python_version=str(row["python_version"]),
        docker_compose_version=_optional_str(row["docker_compose_version"]),
        postgres_version=_optional_str(row["postgres_version"]),
        redis_version=_optional_str(row["redis_version"]),
        nats_version=_optional_str(row["nats_version"]),
        opa_version=_optional_str(row["opa_version"]),
        optional_adapters=dict(row["optional_adapters"]),
        compatibility=dict(row["compatibility"]),
        status=cast(CompatibilityStatus, str(row["status"])),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_migration_baseline(row: RowMapping) -> MigrationBaseline:
    return MigrationBaseline(
        migration_baseline_id=str(row["migration_baseline_id"]),
        schema_version=str(row["schema_version"]),
        migration_count=int(row["migration_count"]),
        migration_hash=str(row["migration_hash"]),
        destructive_migrations=_string_list(row["destructive_migrations"]),
        tables=_string_list(row["tables"]),
        status=cast(MigrationBaselineStatus, str(row["status"])),
        report=dict(row["report"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_release_artifact(row: RowMapping) -> ReleaseArtifactManifest:
    return ReleaseArtifactManifest(
        release_artifact_id=str(row["release_artifact_id"]),
        version=str(row["version"]),
        status=cast(ReleaseArtifactStatus, str(row["status"])),
        artifacts=dict(row["artifacts"]),
        checksums=dict(row["checksums"]),
        report=dict(row["report"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_freeze_gate(row: RowMapping) -> FreezeGateRun:
    return FreezeGateRun(
        freeze_gate_id=str(row["freeze_gate_id"]),
        version=str(row["version"]),
        status=cast(FreezeGateRunStatus, str(row["status"])),
        requested_by=_optional_str(row["requested_by"]),
        checks=[FreezeGateCheck.model_validate(check) for check in _list(row["checks"])],
        failures=_dict_list(row["failures"]),
        warnings=_dict_list(row["warnings"]),
        report=dict(row["report"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _optional_datetime(value: object) -> datetime | None:
    return None if value is None else _datetime(value)


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
