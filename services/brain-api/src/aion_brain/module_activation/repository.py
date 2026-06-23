"""Persistent repository for metadata-only module activation gate records."""

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

from aion_brain.contracts.module_activation import (
    ActivationBlocker,
    ActivationGateRun,
    ActivationPlan,
    ActivationReview,
    ModuleActivationRequest,
    RuntimeRegistrationPreview,
)

module_activation_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_module_activation_requests = Table(
    "aion_module_activation_requests",
    module_activation_metadata,
    Column("activation_request_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("extension_package_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=False),
    Column("capability_binding_ids", json_payload_type, nullable=False),
    Column("readiness_assessment_ids", json_payload_type, nullable=False),
    Column("conformance_run_ids", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("request_type", Text, nullable=False),
    Column("activation_target", Text, nullable=False),
    Column("requested_mode", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("required_approvals", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("required_sandbox_profiles", json_payload_type, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("activation_plan_id", Text, nullable=True),
    Column("registration_preview_id", Text, nullable=True),
    Column("rollback_plan_id", Text, nullable=True),
    Column("activation_allowed", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_activation_requests_trace", "trace_id"),
    Index("ix_aion_activation_requests_actor", "actor_id"),
    Index("ix_aion_activation_requests_workspace", "workspace_id"),
    Index("ix_aion_activation_requests_extension", "extension_package_id"),
    Index("ix_aion_activation_requests_slot", "module_slot_id"),
    Index("ix_aion_activation_requests_status", "status"),
    Index("ix_aion_activation_requests_type", "request_type"),
    Index("ix_aion_activation_requests_target", "activation_target"),
    Index("ix_aion_activation_requests_mode", "requested_mode"),
    Index("ix_aion_activation_requests_risk", "risk_level"),
    Index("ix_aion_activation_requests_activation", "activation_allowed"),
    Index("ix_aion_activation_requests_execution", "execution_allowed"),
    Index("ix_aion_activation_requests_created", "created_at"),
    Index("ix_aion_activation_requests_deleted", "deleted_at"),
)

aion_module_activation_blockers = Table(
    "aion_module_activation_blockers",
    module_activation_metadata,
    Column("activation_blocker_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("activation_request_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("blocker_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("missing_requirement", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("recommended_action", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_activation_blockers_request", "activation_request_id"),
    Index("ix_aion_activation_blockers_slot", "module_slot_id"),
    Index("ix_aion_activation_blockers_binding", "capability_binding_id"),
    Index("ix_aion_activation_blockers_type", "blocker_type"),
    Index("ix_aion_activation_blockers_severity", "severity"),
    Index("ix_aion_activation_blockers_status", "status"),
    Index("ix_aion_activation_blockers_source_type", "source_type"),
    Index("ix_aion_activation_blockers_source_id", "source_id"),
    Index("ix_aion_activation_blockers_created", "created_at"),
)

aion_module_activation_gate_runs = Table(
    "aion_module_activation_gate_runs",
    module_activation_metadata,
    Column("activation_gate_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("activation_request_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("checks_run", json_payload_type, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("activation_allowed", Boolean, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_activation_gate_runs_trace", "trace_id"),
    Index("ix_aion_activation_gate_runs_request", "activation_request_id"),
    Index("ix_aion_activation_gate_runs_status", "status"),
    Index("ix_aion_activation_gate_runs_mode", "mode"),
    Index("ix_aion_activation_gate_runs_score", "score"),
    Index("ix_aion_activation_gate_runs_activation", "activation_allowed"),
    Index("ix_aion_activation_gate_runs_created", "created_at"),
)

aion_module_activation_reviews = Table(
    "aion_module_activation_reviews",
    module_activation_metadata,
    Column("activation_review_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("activation_request_id", Text, nullable=False),
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
    Index("ix_aion_activation_reviews_request", "activation_request_id"),
    Index("ix_aion_activation_reviews_trace", "trace_id"),
    Index("ix_aion_activation_reviews_actor", "actor_id"),
    Index("ix_aion_activation_reviews_workspace", "workspace_id"),
    Index("ix_aion_activation_reviews_status", "status"),
    Index("ix_aion_activation_reviews_decision", "decision"),
    Index("ix_aion_activation_reviews_reviewer", "reviewer_id"),
    Index("ix_aion_activation_reviews_approval", "approval_request_id"),
    Index("ix_aion_activation_reviews_created", "created_at"),
)

aion_module_activation_plans = Table(
    "aion_module_activation_plans",
    module_activation_metadata,
    Column("activation_plan_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("activation_request_id", Text, nullable=False),
    Column("module_slot_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("plan_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("required_contracts", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("required_sandbox_profiles", json_payload_type, nullable=False),
    Column("required_approvals", json_payload_type, nullable=False),
    Column("rollback_plan", json_payload_type, nullable=False),
    Column("blocked", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("executable", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_activation_plans_request", "activation_request_id"),
    Index("ix_aion_activation_plans_slot", "module_slot_id"),
    Index("ix_aion_activation_plans_status", "status"),
    Index("ix_aion_activation_plans_type", "plan_type"),
    Index("ix_aion_activation_plans_blocked", "blocked"),
    Index("ix_aion_activation_plans_executable", "executable"),
    Index("ix_aion_activation_plans_execution", "execution_allowed"),
    Index("ix_aion_activation_plans_created", "created_at"),
)

aion_runtime_registration_previews = Table(
    "aion_runtime_registration_previews",
    module_activation_metadata,
    Column("registration_preview_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("activation_request_id", Text, nullable=True),
    Column("module_slot_id", Text, nullable=True),
    Column("capability_binding_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("preview_type", Text, nullable=False),
    Column("target_runtime", Text, nullable=False),
    Column("target_ref", Text, nullable=True),
    Column("route_previews", json_payload_type, nullable=False),
    Column("capability_previews", json_payload_type, nullable=False),
    Column("policy_action_previews", json_payload_type, nullable=False),
    Column("setting_previews", json_payload_type, nullable=False),
    Column("would_register", Boolean, nullable=False),
    Column("registration_allowed", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_registration_previews_request", "activation_request_id"),
    Index("ix_aion_registration_previews_slot", "module_slot_id"),
    Index("ix_aion_registration_previews_binding", "capability_binding_id"),
    Index("ix_aion_registration_previews_status", "status"),
    Index("ix_aion_registration_previews_type", "preview_type"),
    Index("ix_aion_registration_previews_runtime", "target_runtime"),
    Index("ix_aion_registration_previews_would_register", "would_register"),
    Index("ix_aion_registration_previews_registration", "registration_allowed"),
    Index("ix_aion_registration_previews_created", "created_at"),
)


class ModuleActivationRepository:
    """Store activation gate metadata without activating modules."""

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
            self._engine = _create_engine(database_url)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_request(self, request: ModuleActivationRequest) -> ModuleActivationRequest:
        stored = request.model_copy(update={"created_at": request.created_at or _now()})
        self._replace(
            aion_module_activation_requests,
            "activation_request_id",
            stored.activation_request_id,
            _model_values(aion_module_activation_requests, stored),
        )
        return stored

    def get_request(self, activation_request_id: str) -> ModuleActivationRequest | None:
        return self._get(
            aion_module_activation_requests,
            "activation_request_id",
            activation_request_id,
            ModuleActivationRequest,
        )

    def list_requests(
        self,
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        extension_package_id: str | None = None,
        risk_level: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ModuleActivationRequest]:
        items = self._list(
            aion_module_activation_requests,
            ModuleActivationRequest,
            {
                "status": status,
                "module_slot_id": module_slot_id,
                "extension_package_id": extension_package_id,
                "risk_level": risk_level,
            },
            "created_at",
            limit,
        )
        return items if include_deleted else [item for item in items if item.deleted_at is None]

    def save_blocker(self, blocker: ActivationBlocker) -> ActivationBlocker:
        stored = blocker.model_copy(update={"created_at": blocker.created_at or _now()})
        self._replace(
            aion_module_activation_blockers,
            "activation_blocker_id",
            stored.activation_blocker_id,
            _model_values(aion_module_activation_blockers, stored),
        )
        return stored

    def get_blocker(self, activation_blocker_id: str) -> ActivationBlocker | None:
        return self._get(
            aion_module_activation_blockers,
            "activation_blocker_id",
            activation_blocker_id,
            ActivationBlocker,
        )

    def list_blockers(
        self,
        *,
        activation_request_id: str | None = None,
        module_slot_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ActivationBlocker]:
        return self._list(
            aion_module_activation_blockers,
            ActivationBlocker,
            {
                "activation_request_id": activation_request_id,
                "module_slot_id": module_slot_id,
                "status": status,
                "severity": severity,
            },
            "created_at",
            limit,
        )

    def save_gate_run(self, run: ActivationGateRun) -> ActivationGateRun:
        now = _now()
        stored = run.model_copy(
            update={
                "created_at": run.created_at or now,
                "completed_at": run.completed_at or now,
            }
        )
        self._replace(
            aion_module_activation_gate_runs,
            "activation_gate_run_id",
            stored.activation_gate_run_id,
            _model_values(aion_module_activation_gate_runs, stored),
        )
        return stored

    def list_gate_runs(
        self,
        *,
        activation_request_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ActivationGateRun]:
        return self._list(
            aion_module_activation_gate_runs,
            ActivationGateRun,
            {"activation_request_id": activation_request_id, "status": status},
            "created_at",
            limit,
        )

    def save_review(self, review: ActivationReview) -> ActivationReview:
        stored = review.model_copy(update={"created_at": review.created_at or _now()})
        self._replace(
            aion_module_activation_reviews,
            "activation_review_id",
            stored.activation_review_id,
            _model_values(aion_module_activation_reviews, stored),
        )
        return stored

    def list_reviews(
        self,
        *,
        activation_request_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[ActivationReview]:
        return self._list(
            aion_module_activation_reviews,
            ActivationReview,
            {"activation_request_id": activation_request_id, "decision": decision},
            "created_at",
            limit,
        )

    def save_plan(self, plan: ActivationPlan) -> ActivationPlan:
        stored = plan.model_copy(update={"created_at": plan.created_at or _now()})
        self._replace(
            aion_module_activation_plans,
            "activation_plan_id",
            stored.activation_plan_id,
            _model_values(aion_module_activation_plans, stored),
        )
        return stored

    def get_plan(self, activation_plan_id: str) -> ActivationPlan | None:
        return self._get(
            aion_module_activation_plans,
            "activation_plan_id",
            activation_plan_id,
            ActivationPlan,
        )

    def list_plans(
        self,
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> list[ActivationPlan]:
        return self._list(
            aion_module_activation_plans,
            ActivationPlan,
            {"status": status, "module_slot_id": module_slot_id},
            "created_at",
            limit,
        )

    def save_registration_preview(
        self,
        preview: RuntimeRegistrationPreview,
    ) -> RuntimeRegistrationPreview:
        stored = preview.model_copy(update={"created_at": preview.created_at or _now()})
        self._replace(
            aion_runtime_registration_previews,
            "registration_preview_id",
            stored.registration_preview_id,
            _model_values(aion_runtime_registration_previews, stored),
        )
        return stored

    def get_registration_preview(
        self,
        registration_preview_id: str,
    ) -> RuntimeRegistrationPreview | None:
        return self._get(
            aion_runtime_registration_previews,
            "registration_preview_id",
            registration_preview_id,
            RuntimeRegistrationPreview,
        )

    def list_registration_previews(
        self,
        *,
        activation_request_id: str | None = None,
        module_slot_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RuntimeRegistrationPreview]:
        return self._list(
            aion_runtime_registration_previews,
            RuntimeRegistrationPreview,
            {
                "activation_request_id": activation_request_id,
                "module_slot_id": module_slot_id,
                "status": status,
            },
            "created_at",
            limit,
        )

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        requests = self.list_requests(limit=1000)
        blockers = self.list_blockers(status="open", limit=1000)
        return {
            "status": "blocked" if blockers else "healthy",
            "activation_request_count": len(requests),
            "open_blocker_count": len(blockers),
            "activation_allowed": False,
            "execution_allowed": False,
            "registration_allowed": False,
            "scope": scope or [],
        }

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "module_activation_request",
                item.activation_request_id,
                item.status,
                item.created_at,
            )
            for item in self.list_requests(limit=limit)
        )
        records.extend(
            _registry_record(
                "module_activation_blocker",
                item.activation_blocker_id,
                item.status,
                item.created_at,
            )
            for item in self.list_blockers(limit=limit)
        )
        records.extend(
            _registry_record(
                "module_activation_plan",
                item.activation_plan_id,
                item.status,
                item.created_at,
            )
            for item in self.list_plans(limit=limit)
        )
        records.extend(
            _registry_record(
                "runtime_registration_preview",
                item.registration_preview_id,
                item.status,
                item.created_at,
            )
            for item in self.list_registration_previews(limit=limit)
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

    def _get[T](self, table: Table, key_column: str, key_value: str, model: type[T]) -> T | None:
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
        module_activation_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        engine_kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
        if database_url in {
            "sqlite://",
            "sqlite:///:memory:",
            "sqlite+pysqlite://",
            "sqlite+pysqlite:///:memory:",
        } or ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
        return create_engine(database_url, **engine_kwargs)
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


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
    payload = {key: value for key, value in dict(row).items() if key in fields}
    if model is ActivationGateRun:
        payload["blockers"] = [
            item if isinstance(item, ActivationBlocker) else ActivationBlocker.model_validate(item)
            for item in payload.get("blockers", [])
        ]
    return model(**payload)


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
        "metadata": {
            "activation_allowed": False,
            "execution_allowed": False,
            "registration_allowed": False,
            "module_activation_status": status,
        },
    }


def _now() -> datetime:
    return datetime.now(UTC)


__all__ = [
    "ModuleActivationRepository",
    "aion_module_activation_blockers",
    "aion_module_activation_gate_runs",
    "aion_module_activation_plans",
    "aion_module_activation_requests",
    "aion_module_activation_reviews",
    "aion_runtime_registration_previews",
    "module_activation_metadata",
]
