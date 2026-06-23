"""Persistent repository for model provider hardening metadata."""

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
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.model_provider_hardening import (
    ModelProviderBlocker,
    ModelProviderProfile,
    ModelProviderReadiness,
    ModelProviderSimulation,
    PromptEgressPreview,
)

model_provider_hardening_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_model_provider_profiles = Table(
    "aion_model_provider_profiles",
    model_provider_hardening_metadata,
    Column("provider_profile_id", Text, primary_key=True),
    Column("provider_key", Text, nullable=False, unique=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("provider_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("supported_model_families", json_payload_type, nullable=False),
    Column("supported_modes", json_payload_type, nullable=False),
    Column("declared_capabilities", json_payload_type, nullable=False),
    Column("required_settings", json_payload_type, nullable=False),
    Column("required_policy_actions", json_payload_type, nullable=False),
    Column("egress_requirements", json_payload_type, nullable=False),
    Column("output_governance_requirements", json_payload_type, nullable=False),
    Column("grounding_requirements", json_payload_type, nullable=False),
    Column("tool_use_policy", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("external_calls_allowed", Boolean, nullable=False),
    Column("credentials_required", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_model_provider_profiles_key", "provider_key"),
    Index("ix_aion_model_provider_profiles_status", "status"),
    Index("ix_aion_model_provider_profiles_type", "provider_type"),
    Index("ix_aion_model_provider_profiles_risk", "risk_level"),
    Index("ix_aion_model_provider_profiles_external", "external_calls_allowed"),
    Index("ix_aion_model_provider_profiles_credentials", "credentials_required"),
    Index("ix_aion_model_provider_profiles_created", "created_at"),
)

aion_prompt_egress_previews = Table(
    "aion_prompt_egress_previews",
    model_provider_hardening_metadata,
    Column("prompt_egress_preview_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("provider_profile_id", Text, nullable=True),
    Column("provider_key", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("preview_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("prompt_packet_ref", Text, nullable=True),
    Column("input_manifest_ref", Text, nullable=True),
    Column("redacted_prompt_summary", json_payload_type, nullable=False),
    Column("blocked_fields", json_payload_type, nullable=False),
    Column("egress_allowed", Boolean, nullable=False),
    Column("external_call_allowed", Boolean, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_prompt_egress_previews_trace", "trace_id"),
    Index("ix_aion_prompt_egress_previews_actor", "actor_id"),
    Index("ix_aion_prompt_egress_previews_workspace", "workspace_id"),
    Index("ix_aion_prompt_egress_previews_profile", "provider_profile_id"),
    Index("ix_aion_prompt_egress_previews_key", "provider_key"),
    Index("ix_aion_prompt_egress_previews_status", "status"),
    Index("ix_aion_prompt_egress_previews_type", "preview_type"),
    Index("ix_aion_prompt_egress_previews_egress", "egress_allowed"),
    Index("ix_aion_prompt_egress_previews_external", "external_call_allowed"),
    Index("ix_aion_prompt_egress_previews_created", "created_at"),
)

aion_model_provider_simulations = Table(
    "aion_model_provider_simulations",
    model_provider_hardening_metadata,
    Column("provider_simulation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("provider_profile_id", Text, nullable=True),
    Column("provider_key", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("simulation_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input_manifest_ref", Text, nullable=True),
    Column("egress_preview_id", Text, nullable=True),
    Column("simulated_request_hash", Text, nullable=False),
    Column("simulated_response_hash", Text, nullable=False),
    Column("redacted_simulated_request", json_payload_type, nullable=False),
    Column("redacted_simulated_response", json_payload_type, nullable=False),
    Column("output_governance_status", Text, nullable=False),
    Column("tool_intent_status", Text, nullable=False),
    Column("grounding_status", Text, nullable=False),
    Column("external_calls_made", Boolean, nullable=False),
    Column("credentials_used", Boolean, nullable=False),
    Column("model_invoked", Boolean, nullable=False),
    Column("score", Float, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_model_provider_simulations_trace", "trace_id"),
    Index("ix_aion_model_provider_simulations_profile", "provider_profile_id"),
    Index("ix_aion_model_provider_simulations_key", "provider_key"),
    Index("ix_aion_model_provider_simulations_status", "status"),
    Index("ix_aion_model_provider_simulations_type", "simulation_type"),
    Index("ix_aion_model_provider_simulations_output", "output_governance_status"),
    Index("ix_aion_model_provider_simulations_tool", "tool_intent_status"),
    Index("ix_aion_model_provider_simulations_grounding", "grounding_status"),
    Index("ix_aion_model_provider_simulations_external", "external_calls_made"),
    Index("ix_aion_model_provider_simulations_credentials", "credentials_used"),
    Index("ix_aion_model_provider_simulations_invoked", "model_invoked"),
    Index("ix_aion_model_provider_simulations_score", "score"),
    Index("ix_aion_model_provider_simulations_created", "created_at"),
)

aion_model_provider_readiness_assessments = Table(
    "aion_model_provider_readiness_assessments",
    model_provider_hardening_metadata,
    Column("provider_readiness_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("provider_profile_id", Text, nullable=True),
    Column("provider_key", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("readiness_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("external_call_ready", Boolean, nullable=False),
    Column("credentials_ready", Boolean, nullable=False),
    Column("egress_guard_ready", Boolean, nullable=False),
    Column("output_governance_ready", Boolean, nullable=False),
    Column("tool_intent_guard_ready", Boolean, nullable=False),
    Column("grounding_ready", Boolean, nullable=False),
    Column("policy_ready", Boolean, nullable=False),
    Column("audit_ready", Boolean, nullable=False),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("warning_refs", json_payload_type, nullable=False),
    Column("simulation_refs", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_provider_readiness_trace", "trace_id"),
    Index("ix_aion_provider_readiness_profile", "provider_profile_id"),
    Index("ix_aion_provider_readiness_key", "provider_key"),
    Index("ix_aion_provider_readiness_status", "status"),
    Index("ix_aion_provider_readiness_level", "readiness_level"),
    Index("ix_aion_provider_readiness_external", "external_call_ready"),
    Index("ix_aion_provider_readiness_credentials", "credentials_ready"),
    Index("ix_aion_provider_readiness_score", "score"),
    Index("ix_aion_provider_readiness_created", "created_at"),
)

aion_model_provider_blockers = Table(
    "aion_model_provider_blockers",
    model_provider_hardening_metadata,
    Column("provider_blocker_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("provider_profile_id", Text, nullable=True),
    Column("provider_key", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("blocker_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_provider_blockers_trace", "trace_id"),
    Index("ix_aion_provider_blockers_profile", "provider_profile_id"),
    Index("ix_aion_provider_blockers_key", "provider_key"),
    Index("ix_aion_provider_blockers_source_type", "source_type"),
    Index("ix_aion_provider_blockers_source_id", "source_id"),
    Index("ix_aion_provider_blockers_type", "blocker_type"),
    Index("ix_aion_provider_blockers_severity", "severity"),
    Index("ix_aion_provider_blockers_status", "status"),
    Index("ix_aion_provider_blockers_created", "created_at"),
)


class ModelProviderHardeningRepository:
    """Store provider hardening records without provider calls."""

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

    def save_profile(self, profile: ModelProviderProfile) -> ModelProviderProfile:
        now = _now()
        stored = profile.model_copy(
            update={"created_at": profile.created_at or now, "updated_at": now}
        )
        self._replace(
            aion_model_provider_profiles,
            "provider_profile_id",
            stored.provider_profile_id,
            _model_values(aion_model_provider_profiles, stored),
        )
        return stored

    def get_profile(self, provider_profile_id: str) -> ModelProviderProfile | None:
        return self._get(
            aion_model_provider_profiles,
            "provider_profile_id",
            provider_profile_id,
            ModelProviderProfile,
        )

    def get_profile_by_key(self, provider_key: str) -> ModelProviderProfile | None:
        return self._get(
            aion_model_provider_profiles,
            "provider_key",
            provider_key,
            ModelProviderProfile,
        )

    def list_profiles(
        self,
        *,
        provider_key: str | None = None,
        status: str | None = None,
        risk_level: str | None = None,
        limit: int = 100,
    ) -> list[ModelProviderProfile]:
        return self._list(
            aion_model_provider_profiles,
            ModelProviderProfile,
            {"provider_key": provider_key, "status": status, "risk_level": risk_level},
            "created_at",
            limit,
        )

    def save_egress_preview(self, preview: PromptEgressPreview) -> PromptEgressPreview:
        stored = preview.model_copy(update={"created_at": preview.created_at or _now()})
        self._replace(
            aion_prompt_egress_previews,
            "prompt_egress_preview_id",
            stored.prompt_egress_preview_id,
            _model_values(aion_prompt_egress_previews, stored),
        )
        return stored

    def list_egress_previews(
        self,
        *,
        provider_key: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PromptEgressPreview]:
        return self._list(
            aion_prompt_egress_previews,
            PromptEgressPreview,
            {"provider_key": provider_key, "status": status},
            "created_at",
            limit,
        )

    def save_simulation(self, simulation: ModelProviderSimulation) -> ModelProviderSimulation:
        now = _now()
        stored = simulation.model_copy(
            update={
                "created_at": simulation.created_at or now,
                "completed_at": simulation.completed_at or now,
            }
        )
        self._replace(
            aion_model_provider_simulations,
            "provider_simulation_id",
            stored.provider_simulation_id,
            _model_values(aion_model_provider_simulations, stored),
        )
        return stored

    def get_simulation(self, provider_simulation_id: str) -> ModelProviderSimulation | None:
        return self._get(
            aion_model_provider_simulations,
            "provider_simulation_id",
            provider_simulation_id,
            ModelProviderSimulation,
        )

    def list_simulations(
        self,
        *,
        provider_key: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ModelProviderSimulation]:
        return self._list(
            aion_model_provider_simulations,
            ModelProviderSimulation,
            {"provider_key": provider_key, "status": status},
            "created_at",
            limit,
        )

    def save_readiness(self, readiness: ModelProviderReadiness) -> ModelProviderReadiness:
        now = _now()
        stored = readiness.model_copy(
            update={
                "created_at": readiness.created_at or now,
                "completed_at": readiness.completed_at or now,
            }
        )
        self._replace(
            aion_model_provider_readiness_assessments,
            "provider_readiness_id",
            stored.provider_readiness_id,
            _model_values(aion_model_provider_readiness_assessments, stored),
        )
        return stored

    def list_readiness(
        self,
        *,
        provider_key: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ModelProviderReadiness]:
        return self._list(
            aion_model_provider_readiness_assessments,
            ModelProviderReadiness,
            {"provider_key": provider_key, "status": status},
            "created_at",
            limit,
        )

    def save_blocker(self, blocker: ModelProviderBlocker) -> ModelProviderBlocker:
        stored = blocker.model_copy(update={"created_at": blocker.created_at or _now()})
        self._replace(
            aion_model_provider_blockers,
            "provider_blocker_id",
            stored.provider_blocker_id,
            _model_values(aion_model_provider_blockers, stored),
        )
        return stored

    def get_blocker(self, provider_blocker_id: str) -> ModelProviderBlocker | None:
        return self._get(
            aion_model_provider_blockers,
            "provider_blocker_id",
            provider_blocker_id,
            ModelProviderBlocker,
        )

    def list_blockers(
        self,
        *,
        provider_key: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ModelProviderBlocker]:
        return self._list(
            aion_model_provider_blockers,
            ModelProviderBlocker,
            {"provider_key": provider_key, "status": status, "severity": severity},
            "created_at",
            limit,
        )

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        profiles = self.list_profiles(limit=1000)
        blockers = self.list_blockers(status="open", limit=1000)
        simulations = self.list_simulations(limit=1000)
        critical_blockers = [item for item in blockers if item.severity in {"high", "critical"}]
        return {
            "status": "warning" if critical_blockers else "healthy",
            "provider_profile_count": len(profiles),
            "provider_simulation_count": len(simulations),
            "open_blocker_count": len(blockers),
            "critical_blocker_count": len(critical_blockers),
            "external_model_calls_enabled": False,
            "provider_auth_material_enabled": False,
            "scope": scope or [],
        }

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "model_provider_profile",
                item.provider_profile_id,
                item.status,
                item.created_at,
            )
            for item in self.list_profiles(limit=limit)
        )
        records.extend(
            _registry_record(
                "prompt_egress_preview",
                item.prompt_egress_preview_id,
                item.status,
                item.created_at,
            )
            for item in self.list_egress_previews(limit=limit)
        )
        records.extend(
            _registry_record(
                "model_provider_simulation",
                item.provider_simulation_id,
                item.status,
                item.created_at,
            )
            for item in self.list_simulations(limit=limit)
        )
        records.extend(
            _registry_record(
                "model_provider_readiness",
                item.provider_readiness_id,
                item.status,
                item.created_at,
            )
            for item in self.list_readiness(limit=limit)
        )
        records.extend(
            _registry_record(
                "model_provider_blocker",
                item.provider_blocker_id,
                item.status,
                item.created_at,
            )
            for item in self.list_blockers(limit=limit)
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
            rows = list(connection.execute(statement).mappings().all())
        return [_row_to_model(row, model) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        model_provider_hardening_metadata.create_all(self._engine)
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
    return cast(T, model.model_validate(payload))  # type: ignore[attr-defined]


def _registry_record(
    resource_type: str,
    resource_id: str,
    status: str,
    created_at: datetime | None,
) -> dict[str, Any]:
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "created_at": created_at.isoformat() if created_at else None,
    }


def _now() -> datetime:
    return datetime.now(UTC)


__all__ = ["ModelProviderHardeningRepository", "model_provider_hardening_metadata"]
