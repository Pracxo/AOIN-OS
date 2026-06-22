"""Persistent repository for module slot and capability binding records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.capability_bindings import (
    BindingConflict,
    BindingValidationRun,
    CapabilityBinding,
    ModuleMountPlan,
    RouteBindingPreview,
)
from aion_brain.contracts.module_slots import ModuleSlot

module_binding_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_module_slots = Table(
    "aion_module_slots",
    module_binding_metadata,
    Column("module_slot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("slot_key", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("slot_type", Text, nullable=False),
    Column("lifecycle_state", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("compatibility_status", Text, nullable=False),
    Column("allowed_modes", json_payload_type, nullable=False),
    Column("declared_capability_refs", json_payload_type, nullable=False),
    Column("capability_binding_refs", json_payload_type, nullable=False),
    Column("contract_refs", json_payload_type, nullable=False),
    Column("policy_action_refs", json_payload_type, nullable=False),
    Column("setting_refs", json_payload_type, nullable=False),
    Column("sandbox_profile_id", Text, nullable=True),
    Column("mount_plan_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_slots_extension_package", "extension_package_id"),
    Index("ix_aion_module_slots_slot_key", "slot_key"),
    Index("ix_aion_module_slots_status", "status"),
    Index("ix_aion_module_slots_type", "slot_type"),
    Index("ix_aion_module_slots_lifecycle", "lifecycle_state"),
    Index("ix_aion_module_slots_compat", "compatibility_status"),
    Index("ix_aion_module_slots_sandbox", "sandbox_profile_id"),
    Index("ix_aion_module_slots_mount_plan", "mount_plan_id"),
    Index("ix_aion_module_slots_created_at", "created_at"),
    Index("ix_aion_module_slots_deleted_at", "deleted_at"),
)

aion_capability_bindings = Table(
    "aion_capability_bindings",
    module_binding_metadata,
    Column("capability_binding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=False),
    Column("extension_package_id", Text, nullable=True),
    Column("capability_key", Text, nullable=False),
    Column("capability_type", Text, nullable=False),
    Column("binding_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("route_key", Text, nullable=True),
    Column("target_runtime", Text, nullable=False),
    Column("target_ref", Text, nullable=True),
    Column("risk_level", Text, nullable=False),
    Column("allowed_modes", json_payload_type, nullable=False),
    Column("input_schema", json_payload_type, nullable=False),
    Column("output_schema", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("required_contracts", json_payload_type, nullable=False),
    Column("requires_approval", Boolean, nullable=False),
    Column("requires_sandbox", Boolean, nullable=False),
    Column("sandbox_profile_id", Text, nullable=True),
    Column("dry_run_supported", Boolean, nullable=False),
    Column("controlled_supported", Boolean, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_cap_bindings_slot", "module_slot_id"),
    Index("ix_aion_cap_bindings_extension_package", "extension_package_id"),
    Index("ix_aion_cap_bindings_key", "capability_key"),
    Index("ix_aion_cap_bindings_type", "capability_type"),
    Index("ix_aion_cap_bindings_binding_type", "binding_type"),
    Index("ix_aion_cap_bindings_status", "status"),
    Index("ix_aion_cap_bindings_runtime", "target_runtime"),
    Index("ix_aion_cap_bindings_route", "route_key"),
    Index("ix_aion_cap_bindings_risk", "risk_level"),
    Index("ix_aion_cap_bindings_approval", "requires_approval"),
    Index("ix_aion_cap_bindings_sandbox", "requires_sandbox"),
    Index("ix_aion_cap_bindings_sandbox_profile", "sandbox_profile_id"),
    Index("ix_aion_cap_bindings_created_at", "created_at"),
    Index("ix_aion_cap_bindings_deleted_at", "deleted_at"),
)

aion_binding_validation_runs = Table(
    "aion_binding_validation_runs",
    module_binding_metadata,
    Column("binding_validation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("module_slot_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("capability_binding_ids", json_payload_type, nullable=False),
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
    Index("ix_aion_binding_validations_trace", "trace_id"),
    Index("ix_aion_binding_validations_actor", "actor_id"),
    Index("ix_aion_binding_validations_workspace", "workspace_id"),
    Index("ix_aion_binding_validations_status", "status"),
    Index("ix_aion_binding_validations_mode", "mode"),
    Index("ix_aion_binding_validations_slot", "module_slot_id"),
    Index("ix_aion_binding_validations_extension_package", "extension_package_id"),
    Index("ix_aion_binding_validations_score", "score"),
    Index("ix_aion_binding_validations_created_at", "created_at"),
)

aion_module_mount_plans = Table(
    "aion_module_mount_plans",
    module_binding_metadata,
    Column("mount_plan_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=False),
    Column("extension_package_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("plan_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("required_contracts", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("required_sandbox_profiles", json_payload_type, nullable=False),
    Column("capability_binding_ids", json_payload_type, nullable=False),
    Column("blocked", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("executable", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_mount_plans_slot", "module_slot_id"),
    Index("ix_aion_mount_plans_extension_package", "extension_package_id"),
    Index("ix_aion_mount_plans_status", "status"),
    Index("ix_aion_mount_plans_type", "plan_type"),
    Index("ix_aion_mount_plans_blocked", "blocked"),
    Index("ix_aion_mount_plans_executable", "executable"),
    Index("ix_aion_mount_plans_execution_allowed", "execution_allowed"),
    Index("ix_aion_mount_plans_created_at", "created_at"),
)

aion_route_binding_previews = Table(
    "aion_route_binding_previews",
    module_binding_metadata,
    Column("route_preview_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("route_key", Text, nullable=False),
    Column("route_type", Text, nullable=False),
    Column("method", Text, nullable=True),
    Column("path", Text, nullable=True),
    Column("target_runtime", Text, nullable=False),
    Column("target_ref", Text, nullable=True),
    Column("would_register", Boolean, nullable=False),
    Column("registration_allowed", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_route_previews_slot", "module_slot_id"),
    Index("ix_aion_route_previews_binding", "capability_binding_id"),
    Index("ix_aion_route_previews_status", "status"),
    Index("ix_aion_route_previews_key", "route_key"),
    Index("ix_aion_route_previews_type", "route_type"),
    Index("ix_aion_route_previews_method", "method"),
    Index("ix_aion_route_previews_path", "path"),
    Index("ix_aion_route_previews_runtime", "target_runtime"),
    Index("ix_aion_route_previews_would_register", "would_register"),
    Index("ix_aion_route_previews_registration", "registration_allowed"),
    Index("ix_aion_route_previews_created_at", "created_at"),
)

aion_binding_conflicts = Table(
    "aion_binding_conflicts",
    module_binding_metadata,
    Column("binding_conflict_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("conflict_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("conflicting_refs", json_payload_type, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_binding_conflicts_slot", "module_slot_id"),
    Index("ix_aion_binding_conflicts_binding", "capability_binding_id"),
    Index("ix_aion_binding_conflicts_type", "conflict_type"),
    Index("ix_aion_binding_conflicts_severity", "severity"),
    Index("ix_aion_binding_conflicts_status", "status"),
    Index("ix_aion_binding_conflicts_created_at", "created_at"),
)


class ModuleBindingRepository:
    """Store module binding records without activating modules or capabilities."""

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

    def save_slot(self, slot: ModuleSlot) -> ModuleSlot:
        now = datetime.now(UTC)
        stored = slot.model_copy(update={"created_at": slot.created_at or now, "updated_at": now})
        self._replace(
            aion_module_slots,
            "module_slot_id",
            stored.module_slot_id,
            _model_values(aion_module_slots, stored),
        )
        return stored

    def get_slot(self, module_slot_id: str) -> ModuleSlot | None:
        return self._get(aion_module_slots, "module_slot_id", module_slot_id, ModuleSlot)

    def list_slots(
        self,
        *,
        status: str | None = None,
        slot_type: str | None = None,
        extension_package_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ModuleSlot]:
        items = self._list(
            aion_module_slots,
            ModuleSlot,
            {
                "status": status,
                "slot_type": slot_type,
                "extension_package_id": extension_package_id,
            },
            "created_at",
            limit,
        )
        return items if include_deleted else [item for item in items if item.deleted_at is None]

    def save_binding(self, binding: CapabilityBinding) -> CapabilityBinding:
        now = datetime.now(UTC)
        stored = binding.model_copy(
            update={"created_at": binding.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_capability_bindings,
            "capability_binding_id",
            stored.capability_binding_id,
            _model_values(aion_capability_bindings, stored),
        )
        return stored

    def get_binding(self, capability_binding_id: str) -> CapabilityBinding | None:
        return self._get(
            aion_capability_bindings,
            "capability_binding_id",
            capability_binding_id,
            CapabilityBinding,
        )

    def list_bindings(
        self,
        *,
        module_slot_id: str | None = None,
        status: str | None = None,
        capability_type: str | None = None,
        risk_level: str | None = None,
        extension_package_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[CapabilityBinding]:
        items = self._list(
            aion_capability_bindings,
            CapabilityBinding,
            {
                "module_slot_id": module_slot_id,
                "status": status,
                "capability_type": capability_type,
                "risk_level": risk_level,
                "extension_package_id": extension_package_id,
            },
            "created_at",
            limit,
        )
        return items if include_deleted else [item for item in items if item.deleted_at is None]

    def save_validation_run(self, run: BindingValidationRun) -> BindingValidationRun:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        self._replace(
            aion_binding_validation_runs,
            "binding_validation_id",
            stored.binding_validation_id,
            _model_values(aion_binding_validation_runs, stored),
        )
        return stored

    def get_validation_run(self, binding_validation_id: str) -> BindingValidationRun | None:
        return self._get(
            aion_binding_validation_runs,
            "binding_validation_id",
            binding_validation_id,
            BindingValidationRun,
        )

    def list_validation_runs(
        self,
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> list[BindingValidationRun]:
        return self._list(
            aion_binding_validation_runs,
            BindingValidationRun,
            {
                "status": status,
                "module_slot_id": module_slot_id,
                "extension_package_id": extension_package_id,
            },
            "created_at",
            limit,
        )

    def save_mount_plan(self, plan: ModuleMountPlan) -> ModuleMountPlan:
        stored = plan.model_copy(update={"created_at": plan.created_at or datetime.now(UTC)})
        self._replace(
            aion_module_mount_plans,
            "mount_plan_id",
            stored.mount_plan_id,
            _model_values(aion_module_mount_plans, stored),
        )
        return stored

    def get_mount_plan(self, mount_plan_id: str) -> ModuleMountPlan | None:
        return self._get(aion_module_mount_plans, "mount_plan_id", mount_plan_id, ModuleMountPlan)

    def list_mount_plans(
        self,
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMountPlan]:
        return self._list(
            aion_module_mount_plans,
            ModuleMountPlan,
            {"status": status, "module_slot_id": module_slot_id},
            "created_at",
            limit,
        )

    def save_route_preview(self, preview: RouteBindingPreview) -> RouteBindingPreview:
        stored = preview.model_copy(update={"created_at": preview.created_at or datetime.now(UTC)})
        self._replace(
            aion_route_binding_previews,
            "route_preview_id",
            stored.route_preview_id,
            _model_values(aion_route_binding_previews, stored),
        )
        return stored

    def list_route_previews(
        self,
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RouteBindingPreview]:
        return self._list(
            aion_route_binding_previews,
            RouteBindingPreview,
            {
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
                "status": status,
            },
            "created_at",
            limit,
        )

    def save_conflict(self, conflict: BindingConflict) -> BindingConflict:
        stored = conflict.model_copy(
            update={"created_at": conflict.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_binding_conflicts,
            "binding_conflict_id",
            stored.binding_conflict_id,
            _model_values(aion_binding_conflicts, stored),
        )
        return stored

    def get_conflict(self, binding_conflict_id: str) -> BindingConflict | None:
        return self._get(
            aion_binding_conflicts,
            "binding_conflict_id",
            binding_conflict_id,
            BindingConflict,
        )

    def list_conflicts(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> list[BindingConflict]:
        return self._list(
            aion_binding_conflicts,
            BindingConflict,
            {
                "status": status,
                "severity": severity,
                "module_slot_id": module_slot_id,
                "capability_binding_id": capability_binding_id,
            },
            "created_at",
            limit,
        )

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        slots = self.list_slots(limit=1000)
        bindings = self.list_bindings(limit=1000)
        validations = self.list_validation_runs(limit=1000)
        blocked = [item for item in bindings if item.status == "blocked"]
        pending = [
            item
            for item in validations
            if item.status in {"dry_run", "warning", "failed", "blocked"}
        ]
        return {
            "status": "blocked" if blocked else "warning" if pending else "healthy",
            "module_slot_count": len(slots),
            "capability_binding_count": len(bindings),
            "blocked_binding_count": len(blocked),
            "pending_validation_count": len(pending),
            "scope": scope or [],
        }

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record("module_slot", item.module_slot_id, item.status, item.created_at)
            for item in self.list_slots(limit=limit)
        )
        records.extend(
            _registry_record(
                "capability_binding",
                item.capability_binding_id,
                item.status,
                item.created_at,
            )
            for item in self.list_bindings(limit=limit)
        )
        records.extend(
            _registry_record(
                "module_mount_plan",
                item.mount_plan_id,
                item.status,
                item.created_at,
            )
            for item in self.list_mount_plans(limit=limit)
        )
        records.extend(
            _registry_record(
                "route_binding_preview",
                item.route_preview_id,
                item.status,
                item.created_at,
            )
            for item in self.list_route_previews(limit=limit)
        )
        records.extend(
            _registry_record(
                "binding_validation",
                item.binding_validation_id,
                item.status,
                item.created_at,
            )
            for item in self.list_validation_runs(limit=limit)
        )
        return records[:limit]

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
        module_binding_metadata.create_all(self._engine)
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
) -> dict[str, Any]:
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": "active" if status not in {"archived", "deleted"} else status,
        "created_at": created_at,
        "metadata": {"module_binding_status": status, "source_records_mutated": False},
    }


__all__ = [
    "ModuleBindingRepository",
    "aion_binding_conflicts",
    "aion_binding_validation_runs",
    "aion_capability_bindings",
    "aion_module_mount_plans",
    "aion_module_slots",
    "aion_route_binding_previews",
    "module_binding_metadata",
]
