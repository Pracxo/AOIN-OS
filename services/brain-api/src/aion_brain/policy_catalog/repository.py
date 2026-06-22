"""Persistent repository for policy catalog governance records."""

from __future__ import annotations

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
    UniqueConstraint,
    create_engine,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.policy_catalog import (
    PermissionCatalogEntry,
    PolicyActionCatalogEntry,
    PolicyBundleRecord,
    PolicySimulationRequest,
    PolicySimulationResult,
    PolicyTestCase,
    PolicyTestRun,
    RoleTemplate,
)

policy_catalog_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_policy_action_catalog = Table(
    "aion_policy_action_catalog",
    policy_catalog_metadata,
    Column("policy_action_id", Text, primary_key=True),
    Column("action_type", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("default_risk_level", Text, nullable=False),
    Column("required_permission", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("action_type", name="uq_aion_policy_action_catalog_action_type"),
    Index("ix_aion_policy_action_catalog_action_type", "action_type"),
    Index("ix_aion_policy_action_catalog_category", "category"),
    Index("ix_aion_policy_action_catalog_resource_type", "resource_type"),
    Index("ix_aion_policy_action_catalog_risk", "default_risk_level"),
    Index("ix_aion_policy_action_catalog_permission", "required_permission"),
    Index("ix_aion_policy_action_catalog_status", "status"),
    Index("ix_aion_policy_action_catalog_created_at", "created_at"),
)

aion_permission_catalog = Table(
    "aion_permission_catalog",
    policy_catalog_metadata,
    Column("permission_id", Text, primary_key=True),
    Column("permission", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("action_pattern", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("permission", name="uq_aion_permission_catalog_permission"),
    Index("ix_aion_permission_catalog_permission", "permission"),
    Index("ix_aion_permission_catalog_category", "category"),
    Index("ix_aion_permission_catalog_resource_type", "resource_type"),
    Index("ix_aion_permission_catalog_action_pattern", "action_pattern"),
    Index("ix_aion_permission_catalog_status", "status"),
    Index("ix_aion_permission_catalog_created_at", "created_at"),
)

aion_role_templates = Table(
    "aion_role_templates",
    policy_catalog_metadata,
    Column("role_template_id", Text, primary_key=True),
    Column("role_name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("permissions", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("role_name", name="uq_aion_role_templates_role_name"),
    Index("ix_aion_role_templates_role_name", "role_name"),
    Index("ix_aion_role_templates_status", "status"),
    Index("ix_aion_role_templates_created_at", "created_at"),
)

aion_policy_simulations = Table(
    "aion_policy_simulations",
    policy_catalog_metadata,
    Column("simulation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("input", json_payload_type, nullable=False),
    Column("decision", json_payload_type, nullable=False),
    Column("explanation", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_policy_simulations_trace_id", "trace_id"),
    Index("ix_aion_policy_simulations_actor_id", "actor_id"),
    Index("ix_aion_policy_simulations_workspace_id", "workspace_id"),
    Index("ix_aion_policy_simulations_action_type", "action_type"),
    Index("ix_aion_policy_simulations_resource_type", "resource_type"),
    Index("ix_aion_policy_simulations_created_at", "created_at"),
)

aion_policy_test_cases = Table(
    "aion_policy_test_cases",
    policy_catalog_metadata,
    Column("policy_test_case_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("expected", json_payload_type, nullable=False),
    Column("tags", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_policy_test_cases_name", "name"),
    Index("ix_aion_policy_test_cases_status", "status"),
    Index("ix_aion_policy_test_cases_action_type", "action_type"),
    Index("ix_aion_policy_test_cases_resource_type", "resource_type"),
    Index("ix_aion_policy_test_cases_created_at", "created_at"),
)

aion_policy_test_runs = Table(
    "aion_policy_test_runs",
    policy_catalog_metadata,
    Column("policy_test_run_id", Text, primary_key=True),
    Column("status", Text, nullable=False),
    Column("total_count", Integer, nullable=False),
    Column("passed_count", Integer, nullable=False),
    Column("failed_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("results", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_policy_test_runs_status", "status"),
    Index("ix_aion_policy_test_runs_created_at", "created_at"),
)

aion_policy_bundle_records = Table(
    "aion_policy_bundle_records",
    policy_catalog_metadata,
    Column("policy_bundle_id", Text, primary_key=True),
    Column("bundle_type", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("content", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_policy_bundle_records_bundle_type", "bundle_type"),
    Index("ix_aion_policy_bundle_records_version", "version"),
    Index("ix_aion_policy_bundle_records_hash", "content_hash"),
    Index("ix_aion_policy_bundle_records_status", "status"),
    Index("ix_aion_policy_bundle_records_created_at", "created_at"),
)


class PolicyCatalogRepository:
    """Repository for policy catalog and test harness records."""

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

    def save_action(self, entry: PolicyActionCatalogEntry) -> PolicyActionCatalogEntry:
        """Upsert one action catalog entry."""
        stored = entry.model_copy(update=_timestamps(entry.created_at))
        self._upsert(aion_policy_action_catalog, "action_type", stored.action_type, stored)
        return stored

    def get_action(self, action_type: str) -> PolicyActionCatalogEntry | None:
        row = self._get_by(aion_policy_action_catalog, "action_type", action_type)
        return _row_to_action(row) if row is not None else None

    def list_actions(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> list[PolicyActionCatalogEntry]:
        statement = select(aion_policy_action_catalog)
        if category is not None:
            statement = statement.where(aion_policy_action_catalog.c.category == category)
        if status is not None:
            statement = statement.where(aion_policy_action_catalog.c.status == status)
        return [_row_to_action(row) for row in self._list(statement)]

    def save_permission(self, entry: PermissionCatalogEntry) -> PermissionCatalogEntry:
        """Upsert one permission catalog entry."""
        stored = entry.model_copy(update=_timestamps(entry.created_at))
        self._upsert(aion_permission_catalog, "permission", stored.permission, stored)
        return stored

    def get_permission(self, permission: str) -> PermissionCatalogEntry | None:
        row = self._get_by(aion_permission_catalog, "permission", permission)
        return _row_to_permission(row) if row is not None else None

    def list_permissions(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> list[PermissionCatalogEntry]:
        statement = select(aion_permission_catalog)
        if category is not None:
            statement = statement.where(aion_permission_catalog.c.category == category)
        if status is not None:
            statement = statement.where(aion_permission_catalog.c.status == status)
        return [_row_to_permission(row) for row in self._list(statement)]

    def save_role_template(self, template: RoleTemplate) -> RoleTemplate:
        """Upsert one role template."""
        stored = template.model_copy(update=_timestamps(template.created_at))
        self._upsert(aion_role_templates, "role_name", stored.role_name, stored)
        return stored

    def get_role_template(self, role_name: str) -> RoleTemplate | None:
        row = self._get_by(aion_role_templates, "role_name", role_name)
        return _row_to_role(row) if row is not None else None

    def list_role_templates(self, *, status: str | None = None) -> list[RoleTemplate]:
        statement = select(aion_role_templates)
        if status is not None:
            statement = statement.where(aion_role_templates.c.status == status)
        return [_row_to_role(row) for row in self._list(statement)]

    def save_simulation(self, result: PolicySimulationResult) -> PolicySimulationResult:
        """Persist one simulation result."""
        self._ensure_schema()
        values = {
            "simulation_id": result.simulation_id,
            "trace_id": result.request.trace_id,
            "actor_id": result.request.actor_id,
            "workspace_id": result.request.workspace_id,
            "action_type": result.request.action_type,
            "resource_type": result.request.resource_type,
            "resource_id": result.request.resource_id,
            "input": result.request.model_dump(mode="json"),
            "decision": result.decision.model_dump(mode="json"),
            "explanation": result.explanation,
            "created_at": result.created_at,
        }
        with self._engine.begin() as connection:
            connection.execute(insert(aion_policy_simulations).values(**values))
        return result

    def get_simulation(self, simulation_id: str) -> PolicySimulationResult | None:
        row = self._get_by(aion_policy_simulations, "simulation_id", simulation_id)
        return _row_to_simulation(row) if row is not None else None

    def save_test_case(self, test_case: PolicyTestCase) -> PolicyTestCase:
        """Upsert one test case."""
        stored = test_case.model_copy(update=_timestamps(test_case.created_at))
        self._upsert(
            aion_policy_test_cases,
            "policy_test_case_id",
            stored.policy_test_case_id,
            stored,
        )
        return stored

    def list_test_cases(
        self,
        *,
        status: str | None = None,
        tags: list[str] | None = None,
    ) -> list[PolicyTestCase]:
        statement = select(aion_policy_test_cases)
        if status is not None:
            statement = statement.where(aion_policy_test_cases.c.status == status)
        cases = [_row_to_test_case(row) for row in self._list(statement)]
        if not tags:
            return cases
        required = set(tags)
        return [case for case in cases if required.intersection(set(case.tags))]

    def get_test_case(self, policy_test_case_id: str) -> PolicyTestCase | None:
        row = self._get_by(
            aion_policy_test_cases,
            "policy_test_case_id",
            policy_test_case_id,
        )
        return _row_to_test_case(row) if row is not None else None

    def save_test_run(self, run: PolicyTestRun) -> PolicyTestRun:
        """Persist one policy test run."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_policy_test_runs).values(**run.model_dump(mode="python"))
            )
        return run

    def save_bundle(self, bundle: PolicyBundleRecord) -> PolicyBundleRecord:
        """Persist one policy bundle."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_policy_bundle_records).values(**bundle.model_dump(mode="python"))
            )
        return bundle

    def get_bundle(self, policy_bundle_id: str) -> PolicyBundleRecord | None:
        row = self._get_by(aion_policy_bundle_records, "policy_bundle_id", policy_bundle_id)
        return _row_to_bundle(row) if row is not None else None

    def list_bundles(self, *, bundle_type: str | None = None) -> list[PolicyBundleRecord]:
        statement = select(aion_policy_bundle_records)
        if bundle_type is not None:
            statement = statement.where(aion_policy_bundle_records.c.bundle_type == bundle_type)
        return [_row_to_bundle(row) for row in self._list(statement)]

    def _upsert(
        self,
        table: Table,
        natural_key: str,
        natural_value: str,
        model: object,
    ) -> None:
        self._ensure_schema()
        values = cast(Any, model).model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[natural_key]).where(table.c[natural_key] == natural_value)
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[natural_key] == natural_value).values(**values)
                )

    def _get_by(self, table: Table, column_name: str, value: str) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(table.c[column_name] == value))
                .mappings()
                .first()
            )
        return row

    def _list(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        statement = statement.order_by(text("created_at"))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return list(rows)

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            policy_catalog_metadata.create_all(self._engine)
        self._schema_ready = True


def _timestamps(existing_created_at: datetime | None) -> dict[str, datetime]:
    now = datetime.now(UTC)
    return {"created_at": existing_created_at or now, "updated_at": now}


def _row_to_action(row: RowMapping) -> PolicyActionCatalogEntry:
    return PolicyActionCatalogEntry(**dict(row))


def _row_to_permission(row: RowMapping) -> PermissionCatalogEntry:
    return PermissionCatalogEntry(**dict(row))


def _row_to_role(row: RowMapping) -> RoleTemplate:
    return RoleTemplate(**dict(row))


def _row_to_simulation(row: RowMapping) -> PolicySimulationResult:
    request = PolicySimulationRequest.model_validate(row["input"])
    return PolicySimulationResult(
        simulation_id=str(row["simulation_id"]),
        request=request,
        decision=PolicyDecision.model_validate(row["decision"]),
        explanation=dict(row["explanation"]),
        created_at=cast(datetime, row["created_at"]),
    )


def _row_to_test_case(row: RowMapping) -> PolicyTestCase:
    return PolicyTestCase(**dict(row))


def _row_to_bundle(row: RowMapping) -> PolicyBundleRecord:
    return PolicyBundleRecord(**dict(row))
