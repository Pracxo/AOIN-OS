"""Persistent repository for AION Extension Registry records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
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
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.extension_compatibility import ExtensionCompatibilityRun
from aion_brain.contracts.extensions import (
    ExtensionCapabilityDeclaration,
    ExtensionDependencyDeclaration,
    ExtensionInstallPlan,
    ExtensionIntakeRun,
    ExtensionPackage,
    ExtensionReview,
)

extension_registry_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_extension_packages = Table(
    "aion_extension_packages",
    extension_registry_metadata,
    Column("extension_package_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("extension_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("package_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_ref", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("manifest_hash", Text, nullable=False),
    Column("manifest", json_payload_type, nullable=False),
    Column("declared_capabilities", json_payload_type, nullable=False),
    Column("declared_contracts", json_payload_type, nullable=False),
    Column("declared_dependencies", json_payload_type, nullable=False),
    Column("declared_policy_actions", json_payload_type, nullable=False),
    Column("declared_settings", json_payload_type, nullable=False),
    Column("declared_routes", json_payload_type, nullable=False),
    Column("declared_events", json_payload_type, nullable=False),
    Column("declared_resources", json_payload_type, nullable=False),
    Column("compatibility_status", Text, nullable=False),
    Column("review_status", Text, nullable=False),
    Column("install_plan_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_extension_packages_extension_key", "extension_key"),
    Index("ix_aion_extension_packages_name", "name"),
    Index("ix_aion_extension_packages_version", "version"),
    Index("ix_aion_extension_packages_status", "status"),
    Index("ix_aion_extension_packages_package_type", "package_type"),
    Index("ix_aion_extension_packages_source_type", "source_type"),
    Index("ix_aion_extension_packages_manifest_hash", "manifest_hash"),
    Index("ix_aion_extension_packages_compatibility_status", "compatibility_status"),
    Index("ix_aion_extension_packages_review_status", "review_status"),
    Index("ix_aion_extension_packages_created_at", "created_at"),
    Index("ix_aion_extension_packages_deleted_at", "deleted_at"),
)

aion_extension_capability_declarations = Table(
    "aion_extension_capability_declarations",
    extension_registry_metadata,
    Column("capability_declaration_id", Text, primary_key=True),
    Column(
        "extension_package_id",
        Text,
        ForeignKey("aion_extension_packages.extension_package_id"),
        nullable=False,
    ),
    Column("capability_key", Text, nullable=False),
    Column("capability_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("requires_policy", Boolean, nullable=False),
    Column("requires_approval", Boolean, nullable=False),
    Column("requires_sandbox", Boolean, nullable=False),
    Column("dry_run_supported", Boolean, nullable=False),
    Column("controlled_supported", Boolean, nullable=False),
    Column("input_schema", json_payload_type, nullable=False),
    Column("output_schema", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_ext_cap_package", "extension_package_id"),
    Index("ix_aion_ext_cap_key", "capability_key"),
    Index("ix_aion_ext_cap_type", "capability_type"),
    Index("ix_aion_ext_cap_status", "status"),
    Index("ix_aion_ext_cap_risk", "risk_level"),
    Index("ix_aion_ext_cap_requires_policy", "requires_policy"),
    Index("ix_aion_ext_cap_requires_approval", "requires_approval"),
    Index("ix_aion_ext_cap_requires_sandbox", "requires_sandbox"),
    Index("ix_aion_ext_cap_created_at", "created_at"),
)

aion_extension_dependency_declarations = Table(
    "aion_extension_dependency_declarations",
    extension_registry_metadata,
    Column("dependency_declaration_id", Text, primary_key=True),
    Column(
        "extension_package_id",
        Text,
        ForeignKey("aion_extension_packages.extension_package_id"),
        nullable=False,
    ),
    Column("dependency_key", Text, nullable=False),
    Column("dependency_type", Text, nullable=False),
    Column("version_constraint", Text, nullable=True),
    Column("required", Boolean, nullable=False),
    Column("status", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_ext_dep_package", "extension_package_id"),
    Index("ix_aion_ext_dep_key", "dependency_key"),
    Index("ix_aion_ext_dep_type", "dependency_type"),
    Index("ix_aion_ext_dep_required", "required"),
    Index("ix_aion_ext_dep_status", "status"),
    Index("ix_aion_ext_dep_source", "source"),
    Index("ix_aion_ext_dep_created_at", "created_at"),
)

aion_extension_compatibility_runs = Table(
    "aion_extension_compatibility_runs",
    extension_registry_metadata,
    Column("extension_compatibility_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column(
        "extension_package_id",
        Text,
        ForeignKey("aion_extension_packages.extension_package_id"),
        nullable=False,
    ),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("contract_snapshot_id", Text, nullable=True),
    Column("compatibility_scan_id", Text, nullable=True),
    Column("checks", json_payload_type, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_ext_compat_trace", "trace_id"),
    Index("ix_aion_ext_compat_package", "extension_package_id"),
    Index("ix_aion_ext_compat_status", "status"),
    Index("ix_aion_ext_compat_mode", "mode"),
    Index("ix_aion_ext_compat_snapshot", "contract_snapshot_id"),
    Index("ix_aion_ext_compat_scan", "compatibility_scan_id"),
    Index("ix_aion_ext_compat_score", "score"),
    Index("ix_aion_ext_compat_created_at", "created_at"),
)

aion_extension_intake_runs = Table(
    "aion_extension_intake_runs",
    extension_registry_metadata,
    Column("extension_intake_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("extension_package", json_payload_type, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("manifest_hash", Text, nullable=False),
    Column("validation_status", Text, nullable=False),
    Column("compatibility_status", Text, nullable=False),
    Column("review_required", Boolean, nullable=False),
    Column("install_plan_created", Boolean, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_ext_intake_trace", "trace_id"),
    Index("ix_aion_ext_intake_actor", "actor_id"),
    Index("ix_aion_ext_intake_workspace", "workspace_id"),
    Index("ix_aion_ext_intake_status", "status"),
    Index("ix_aion_ext_intake_mode", "mode"),
    Index("ix_aion_ext_intake_package", "extension_package_id"),
    Index("ix_aion_ext_intake_manifest_hash", "manifest_hash"),
    Index("ix_aion_ext_intake_validation", "validation_status"),
    Index("ix_aion_ext_intake_compat", "compatibility_status"),
    Index("ix_aion_ext_intake_review", "review_required"),
    Index("ix_aion_ext_intake_created_at", "created_at"),
)

aion_extension_reviews = Table(
    "aion_extension_reviews",
    extension_registry_metadata,
    Column("extension_review_id", Text, primary_key=True),
    Column(
        "extension_package_id",
        Text,
        ForeignKey("aion_extension_packages.extension_package_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("decision", Text, nullable=False),
    Column("reviewer_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("approval_request_id", Text, nullable=True),
    Column("policy_decision_id", Text, nullable=True),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_ext_reviews_package", "extension_package_id"),
    Index("ix_aion_ext_reviews_trace", "trace_id"),
    Index("ix_aion_ext_reviews_actor", "actor_id"),
    Index("ix_aion_ext_reviews_workspace", "workspace_id"),
    Index("ix_aion_ext_reviews_status", "status"),
    Index("ix_aion_ext_reviews_decision", "decision"),
    Index("ix_aion_ext_reviews_reviewer", "reviewer_id"),
    Index("ix_aion_ext_reviews_approval", "approval_request_id"),
    Index("ix_aion_ext_reviews_created_at", "created_at"),
)

aion_extension_install_plans = Table(
    "aion_extension_install_plans",
    extension_registry_metadata,
    Column("install_plan_id", Text, primary_key=True),
    Column(
        "extension_package_id",
        Text,
        ForeignKey("aion_extension_packages.extension_package_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("plan_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("required_approvals", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("required_contracts", json_payload_type, nullable=False),
    Column("required_sandbox_profiles", json_payload_type, nullable=False),
    Column("blocked", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("executable", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_ext_plans_package", "extension_package_id"),
    Index("ix_aion_ext_plans_trace", "trace_id"),
    Index("ix_aion_ext_plans_status", "status"),
    Index("ix_aion_ext_plans_type", "plan_type"),
    Index("ix_aion_ext_plans_blocked", "blocked"),
    Index("ix_aion_ext_plans_executable", "executable"),
    Index("ix_aion_ext_plans_execution_allowed", "execution_allowed"),
    Index("ix_aion_ext_plans_created_at", "created_at"),
)


class ExtensionRegistryRepository:
    """Store extension registry records without loading extension code."""

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
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_package(self, package: ExtensionPackage) -> ExtensionPackage:
        now = datetime.now(UTC)
        stored = package.model_copy(
            update={
                "created_at": package.created_at or now,
                "updated_at": now,
            }
        )
        self._replace(
            aion_extension_packages,
            "extension_package_id",
            stored.extension_package_id,
            _model_values(aion_extension_packages, stored),
        )
        return stored

    def get_package(self, extension_package_id: str) -> ExtensionPackage | None:
        return self._get(
            aion_extension_packages,
            "extension_package_id",
            extension_package_id,
            ExtensionPackage,
        )

    def list_packages(
        self,
        *,
        status: str | None = None,
        package_type: str | None = None,
        compatibility_status: str | None = None,
        review_status: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ExtensionPackage]:
        filters: dict[str, object | None] = {
            "status": status,
            "package_type": package_type,
            "compatibility_status": compatibility_status,
            "review_status": review_status,
        }
        items = self._list(aion_extension_packages, ExtensionPackage, filters, "created_at", limit)
        return items if include_deleted else [item for item in items if item.deleted_at is None]

    def save_capability_declaration(
        self, declaration: ExtensionCapabilityDeclaration
    ) -> ExtensionCapabilityDeclaration:
        stored = declaration.model_copy(
            update={"created_at": declaration.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_extension_capability_declarations,
            "capability_declaration_id",
            stored.capability_declaration_id,
            _model_values(aion_extension_capability_declarations, stored),
        )
        return stored

    def list_capability_declarations(
        self, extension_package_id: str | None = None, *, limit: int = 100
    ) -> list[ExtensionCapabilityDeclaration]:
        return self._list(
            aion_extension_capability_declarations,
            ExtensionCapabilityDeclaration,
            {"extension_package_id": extension_package_id},
            "created_at",
            limit,
        )

    def save_dependency_declaration(
        self, declaration: ExtensionDependencyDeclaration
    ) -> ExtensionDependencyDeclaration:
        stored = declaration.model_copy(
            update={"created_at": declaration.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_extension_dependency_declarations,
            "dependency_declaration_id",
            stored.dependency_declaration_id,
            _model_values(aion_extension_dependency_declarations, stored),
        )
        return stored

    def list_dependency_declarations(
        self, extension_package_id: str | None = None, *, limit: int = 100
    ) -> list[ExtensionDependencyDeclaration]:
        return self._list(
            aion_extension_dependency_declarations,
            ExtensionDependencyDeclaration,
            {"extension_package_id": extension_package_id},
            "created_at",
            limit,
        )

    def save_compatibility_run(self, run: ExtensionCompatibilityRun) -> ExtensionCompatibilityRun:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        self._replace(
            aion_extension_compatibility_runs,
            "extension_compatibility_id",
            stored.extension_compatibility_id,
            _model_values(aion_extension_compatibility_runs, stored),
        )
        return stored

    def get_compatibility_run(
        self, extension_compatibility_id: str
    ) -> ExtensionCompatibilityRun | None:
        return self._get(
            aion_extension_compatibility_runs,
            "extension_compatibility_id",
            extension_compatibility_id,
            ExtensionCompatibilityRun,
        )

    def list_compatibility_runs(
        self,
        *,
        extension_package_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ExtensionCompatibilityRun]:
        return self._list(
            aion_extension_compatibility_runs,
            ExtensionCompatibilityRun,
            {"extension_package_id": extension_package_id, "status": status},
            "created_at",
            limit,
        )

    def save_intake_run(self, run: ExtensionIntakeRun) -> ExtensionIntakeRun:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        values = _model_values(aion_extension_intake_runs, stored)
        values["extension_package_id"] = (
            stored.extension_package.extension_package_id if stored.extension_package else None
        )
        self._replace(
            aion_extension_intake_runs,
            "extension_intake_id",
            stored.extension_intake_id,
            values,
        )
        return stored

    def get_intake_run(self, extension_intake_id: str) -> ExtensionIntakeRun | None:
        return self._get(
            aion_extension_intake_runs,
            "extension_intake_id",
            extension_intake_id,
            ExtensionIntakeRun,
        )

    def list_intake_runs(self, *, limit: int = 100) -> list[ExtensionIntakeRun]:
        return self._list(aion_extension_intake_runs, ExtensionIntakeRun, {}, "created_at", limit)

    def save_review(self, review: ExtensionReview) -> ExtensionReview:
        stored = review.model_copy(update={"created_at": review.created_at or datetime.now(UTC)})
        self._replace(
            aion_extension_reviews,
            "extension_review_id",
            stored.extension_review_id,
            _model_values(aion_extension_reviews, stored),
        )
        return stored

    def list_reviews(
        self,
        *,
        extension_package_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[ExtensionReview]:
        return self._list(
            aion_extension_reviews,
            ExtensionReview,
            {"extension_package_id": extension_package_id, "decision": decision},
            "created_at",
            limit,
        )

    def save_install_plan(self, plan: ExtensionInstallPlan) -> ExtensionInstallPlan:
        stored = plan.model_copy(update={"created_at": plan.created_at or datetime.now(UTC)})
        self._replace(
            aion_extension_install_plans,
            "install_plan_id",
            stored.install_plan_id,
            _model_values(aion_extension_install_plans, stored),
        )
        return stored

    def get_install_plan(self, install_plan_id: str) -> ExtensionInstallPlan | None:
        return self._get(
            aion_extension_install_plans,
            "install_plan_id",
            install_plan_id,
            ExtensionInstallPlan,
        )

    def list_install_plans(
        self,
        *,
        status: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> list[ExtensionInstallPlan]:
        return self._list(
            aion_extension_install_plans,
            ExtensionInstallPlan,
            {"status": status, "extension_package_id": extension_package_id},
            "created_at",
            limit,
        )

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "extension_package",
                item.extension_package_id,
                item.status,
                item.created_at,
                {
                    "extension_key": item.extension_key,
                    "version": item.version,
                    "compatibility_status": item.compatibility_status,
                    "review_status": item.review_status,
                },
            )
            for item in self.list_packages(limit=limit)
        )
        records.extend(
            _registry_record(
                "extension_compatibility",
                item.extension_compatibility_id,
                item.status,
                item.created_at,
                {"extension_package_id": item.extension_package_id, "score": item.score},
            )
            for item in self.list_compatibility_runs(limit=limit)
        )
        records.extend(
            _registry_record(
                "extension_install_plan",
                item.install_plan_id,
                item.status,
                item.created_at,
                {
                    "extension_package_id": item.extension_package_id,
                    "blocked": item.blocked,
                    "executable": item.executable,
                },
            )
            for item in self.list_install_plans(limit=limit)
        )
        return records[:limit]

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        packages = self.list_packages(limit=1000)
        blocked = [item for item in packages if item.compatibility_status == "blocked"]
        pending = [item for item in packages if item.review_status == "pending"]
        return {
            "status": "blocked" if blocked else "warning" if pending else "healthy",
            "package_count": len(packages),
            "blocked_count": len(blocked),
            "pending_review_count": len(pending),
            "scope": scope or [],
        }

    def _replace(
        self,
        table: Table,
        key_column: str,
        key_value: str,
        values: dict[str, Any],
    ) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key_column]).where(table.c[key_column] == key_value)
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key_column] == key_value).values(**values)
                )

    def _get[T](
        self,
        table: Table,
        key_column: str,
        key_value: str,
        model: type[T],
    ) -> T | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(table.c[key_column] == key_value))
                .mappings()
                .first()
            )
        return _row_to_model(row, model) if row is not None else None

    def _list[T](
        self,
        table: Table,
        model: type[T],
        filters: dict[str, object | None],
        order_column: str,
        limit: int,
    ) -> list[T]:
        self._ensure_schema()
        statement = select(table).order_by(getattr(table.c, order_column).desc()).limit(limit)
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(table.c, column) == value)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_model(row, model) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        extension_registry_metadata.create_all(self._engine)
        self._schema_ready = True


def _model_values(table: Table, model: Any) -> dict[str, Any]:
    python_data = model.model_dump(mode="python")
    json_data = model.model_dump(mode="json")
    values: dict[str, Any] = {}
    for column in table.columns:
        if column.name not in python_data:
            continue
        value = python_data[column.name]
        values[column.name] = json_data[column.name] if isinstance(value, (dict, list)) else value
    return values


def _row_to_model[T](row: RowMapping, model: type[T]) -> T:
    fields = getattr(model, "model_fields", {})
    return model(**{key: value for key, value in dict(row).items() if key in fields})


def _registry_record(
    resource_type: str,
    resource_id: str,
    status: str,
    created_at: datetime | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    registry_metadata = dict(metadata)
    registry_metadata["extension_registry_status"] = status
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": _resource_registry_status(status),
        "created_at": created_at,
        "metadata": registry_metadata,
        "source_records_mutated": False,
    }


def _resource_registry_status(status: str) -> str:
    if status in {"archived", "deleted", "missing", "stale", "unknown"}:
        return status
    return "active"


__all__ = [
    "ExtensionRegistryRepository",
    "aion_extension_capability_declarations",
    "aion_extension_compatibility_runs",
    "aion_extension_dependency_declarations",
    "aion_extension_install_plans",
    "aion_extension_intake_runs",
    "aion_extension_packages",
    "aion_extension_reviews",
    "extension_registry_metadata",
]
