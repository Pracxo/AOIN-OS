"""Persistent repository for sandbox control-plane records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
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

from aion_brain.contracts.sandbox import (
    ResourceLimits,
    RuntimeGrantStatus,
    RuntimePermission,
    RuntimePermissionGrant,
    SandboxProfile,
    SandboxRunRequest,
    SandboxRunResult,
    SandboxStatus,
    SandboxType,
    SandboxValidationResult,
)

sandbox_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_sandbox_profiles = Table(
    "aion_sandbox_profiles",
    sandbox_metadata,
    Column("sandbox_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("sandbox_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("resource_limits", json_payload_type, nullable=False),
    Column("egress_rules", json_payload_type, nullable=False),
    Column("filesystem_rules", json_payload_type, nullable=False),
    Column("allowed_runtime_permissions", json_payload_type, nullable=False),
    Column("secret_refs_allowed", json_payload_type, nullable=False),
    Column("connector_refs_allowed", json_payload_type, nullable=False),
    Column("network_enabled", Boolean, nullable=False),
    Column("filesystem_write_enabled", Boolean, nullable=False),
    Column("process_spawn_enabled", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_sandbox_profiles_name", "name"),
    Index("ix_aion_sandbox_profiles_status", "status"),
    Index("ix_aion_sandbox_profiles_sandbox_type", "sandbox_type"),
    Index("ix_aion_sandbox_profiles_network_enabled", "network_enabled"),
    Index("ix_aion_sandbox_profiles_process_spawn_enabled", "process_spawn_enabled"),
    Index("ix_aion_sandbox_profiles_created_at", "created_at"),
)

aion_runtime_permission_grants = Table(
    "aion_runtime_permission_grants",
    sandbox_metadata,
    Column("runtime_permission_id", Text, primary_key=True),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("sandbox_profile_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("permissions", json_payload_type, nullable=False),
    Column("secret_refs", json_payload_type, nullable=False),
    Column("connector_refs", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("granted_by", Text, nullable=True),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_runtime_permission_grants_target_type", "target_type"),
    Index("ix_aion_runtime_permission_grants_target_id", "target_id"),
    Index("ix_aion_runtime_permission_grants_sandbox_profile_id", "sandbox_profile_id"),
    Index("ix_aion_runtime_permission_grants_status", "status"),
    Index("ix_aion_runtime_permission_grants_expires_at", "expires_at"),
    Index("ix_aion_runtime_permission_grants_created_at", "created_at"),
)

aion_sandbox_validation_records = Table(
    "aion_sandbox_validation_records",
    sandbox_metadata,
    Column("validation_id", Text, primary_key=True),
    Column("sandbox_profile_id", Text, nullable=True),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("score", Float, nullable=False),
    Column("checks", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_sandbox_validation_records_profile", "sandbox_profile_id"),
    Index("ix_aion_sandbox_validation_records_target_type", "target_type"),
    Index("ix_aion_sandbox_validation_records_target_id", "target_id"),
    Index("ix_aion_sandbox_validation_records_status", "status"),
    Index("ix_aion_sandbox_validation_records_score", "score"),
    Index("ix_aion_sandbox_validation_records_created_at", "created_at"),
)

aion_sandbox_runs = Table(
    "aion_sandbox_runs",
    sandbox_metadata,
    Column("sandbox_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("sandbox_profile_id", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_sandbox_runs_trace_id", "trace_id"),
    Index("ix_aion_sandbox_runs_actor_id", "actor_id"),
    Index("ix_aion_sandbox_runs_workspace_id", "workspace_id"),
    Index("ix_aion_sandbox_runs_profile", "sandbox_profile_id"),
    Index("ix_aion_sandbox_runs_target_type", "target_type"),
    Index("ix_aion_sandbox_runs_target_id", "target_id"),
    Index("ix_aion_sandbox_runs_mode", "mode"),
    Index("ix_aion_sandbox_runs_status", "status"),
    Index("ix_aion_sandbox_runs_created_at", "created_at"),
)


class SandboxRepository:
    """Repository for sandbox profiles, grants, validation, and run records."""

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

    def save_profile(self, profile: SandboxProfile) -> SandboxProfile:
        """Upsert one sandbox profile."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = profile.model_dump(mode="python")
        values["resource_limits"] = profile.resource_limits.model_dump(mode="python")
        values["egress_rules"] = [rule.model_dump(mode="python") for rule in profile.egress_rules]
        values["filesystem_rules"] = [
            rule.model_dump(mode="python") for rule in profile.filesystem_rules
        ]
        values["allowed_runtime_permissions"] = [
            permission.model_dump(mode="python")
            for permission in profile.allowed_runtime_permissions
        ]
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = profile.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_sandbox_profiles.c.sandbox_profile_id).where(
                    aion_sandbox_profiles.c.sandbox_profile_id == profile.sandbox_profile_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_sandbox_profiles).values(**values))
            else:
                connection.execute(
                    update(aion_sandbox_profiles)
                    .where(aion_sandbox_profiles.c.sandbox_profile_id == profile.sandbox_profile_id)
                    .values(**values)
                )
        return stored

    def get_profile(self, sandbox_profile_id: str) -> SandboxProfile | None:
        """Return one sandbox profile."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_sandbox_profiles).where(
                    aion_sandbox_profiles.c.sandbox_profile_id == sandbox_profile_id
                )
            ).mappings().first()
        return _row_to_profile(row) if row is not None else None

    def list_profiles(self, status: str | None = None) -> list[SandboxProfile]:
        """List sandbox profiles."""
        self._ensure_schema()
        statement = select(aion_sandbox_profiles)
        if status is not None:
            statement = statement.where(aion_sandbox_profiles.c.status == status)
        statement = statement.order_by(aion_sandbox_profiles.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_profile(row) for row in rows]

    def save_validation(self, result: SandboxValidationResult) -> SandboxValidationResult:
        """Persist a validation result."""
        self._ensure_schema()
        values = result.model_dump(mode="python")
        values["checks"] = [check.model_dump(mode="python") for check in result.checks]
        values["created_at"] = values["created_at"] or datetime.now(UTC)
        stored = result.model_copy(update={"created_at": values["created_at"]})
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_sandbox_validation_records.c.validation_id).where(
                    aion_sandbox_validation_records.c.validation_id == result.validation_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_sandbox_validation_records).values(**values))
            else:
                connection.execute(
                    update(aion_sandbox_validation_records)
                    .where(
                        aion_sandbox_validation_records.c.validation_id
                        == result.validation_id
                    )
                    .values(**values)
                )
        return stored

    def save_run(
        self,
        request: SandboxRunRequest,
        result: SandboxRunResult,
    ) -> SandboxRunResult:
        """Persist a sandbox run result with the request input envelope."""
        self._ensure_schema()
        values = result.model_dump(mode="python")
        values["actor_id"] = request.actor_id
        values["workspace_id"] = request.workspace_id
        values["input"] = request.input
        values["created_at"] = values["created_at"] or datetime.now(UTC)
        stored = result.model_copy(update={"created_at": values["created_at"]})
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_sandbox_runs.c.sandbox_run_id).where(
                    aion_sandbox_runs.c.sandbox_run_id == result.sandbox_run_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_sandbox_runs).values(**values))
            else:
                connection.execute(
                    update(aion_sandbox_runs)
                    .where(aion_sandbox_runs.c.sandbox_run_id == result.sandbox_run_id)
                    .values(**values)
                )
        return stored

    def save_runtime_permission(
        self,
        grant: RuntimePermissionGrant,
    ) -> RuntimePermissionGrant:
        """Upsert a runtime permission grant."""
        self._ensure_schema()
        values = grant.model_dump(mode="python")
        values["permissions"] = [
            permission.model_dump(mode="python") for permission in grant.permissions
        ]
        values["created_at"] = values["created_at"] or datetime.now(UTC)
        stored = grant.model_copy(update={"created_at": values["created_at"]})
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_runtime_permission_grants.c.runtime_permission_id).where(
                    aion_runtime_permission_grants.c.runtime_permission_id
                    == grant.runtime_permission_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_runtime_permission_grants).values(**values))
            else:
                connection.execute(
                    update(aion_runtime_permission_grants)
                    .where(
                        aion_runtime_permission_grants.c.runtime_permission_id
                        == grant.runtime_permission_id
                    )
                    .values(**values)
                )
        return stored

    def get_runtime_permission(
        self,
        runtime_permission_id: str,
    ) -> RuntimePermissionGrant | None:
        """Return one runtime permission grant."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_runtime_permission_grants).where(
                    aion_runtime_permission_grants.c.runtime_permission_id
                    == runtime_permission_id
                )
            ).mappings().first()
        return _row_to_grant(row) if row is not None else None

    def list_runtime_permissions(
        self,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
        status: str | None = None,
    ) -> list[RuntimePermissionGrant]:
        """List runtime permission grants."""
        self._ensure_schema()
        statement = select(aion_runtime_permission_grants)
        if target_type is not None:
            statement = statement.where(aion_runtime_permission_grants.c.target_type == target_type)
        if target_id is not None:
            statement = statement.where(aion_runtime_permission_grants.c.target_id == target_id)
        if status is not None:
            statement = statement.where(aion_runtime_permission_grants.c.status == status)
        statement = statement.order_by(aion_runtime_permission_grants.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_grant(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            sandbox_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_profile(row: RowMapping) -> SandboxProfile:
    return SandboxProfile(
        sandbox_profile_id=str(row["sandbox_profile_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(SandboxStatus, str(row["status"])),
        sandbox_type=cast(SandboxType, str(row["sandbox_type"])),
        owner_scope=list(row["owner_scope"]),
        resource_limits=ResourceLimits.model_validate(row["resource_limits"]),
        egress_rules=list(row["egress_rules"]),
        filesystem_rules=list(row["filesystem_rules"]),
        allowed_runtime_permissions=[
            RuntimePermission.model_validate(item)
            for item in list(row["allowed_runtime_permissions"])
        ],
        secret_refs_allowed=list(row["secret_refs_allowed"]),
        connector_refs_allowed=list(row["connector_refs_allowed"]),
        network_enabled=bool(row["network_enabled"]),
        filesystem_write_enabled=bool(row["filesystem_write_enabled"]),
        process_spawn_enabled=bool(row["process_spawn_enabled"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _row_to_grant(row: RowMapping) -> RuntimePermissionGrant:
    return RuntimePermissionGrant(
        runtime_permission_id=str(row["runtime_permission_id"]),
        target_type=cast(Any, str(row["target_type"])),
        target_id=str(row["target_id"]),
        sandbox_profile_id=_optional_str(row["sandbox_profile_id"]),
        owner_scope=list(row["owner_scope"]),
        permissions=[RuntimePermission.model_validate(item) for item in list(row["permissions"])],
        secret_refs=list(row["secret_refs"]),
        connector_refs=list(row["connector_refs"]),
        status=cast(RuntimeGrantStatus, str(row["status"])),
        granted_by=_optional_str(row["granted_by"]),
        expires_at=_optional_datetime(row["expires_at"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        revoked_at=_optional_datetime(row["revoked_at"]),
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


__all__ = [
    "SandboxRepository",
    "aion_runtime_permission_grants",
    "aion_sandbox_profiles",
    "aion_sandbox_runs",
    "aion_sandbox_validation_records",
    "sandbox_metadata",
]
