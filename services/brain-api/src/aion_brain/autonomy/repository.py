"""Autonomy Governor persistence."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
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
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.autonomy import (
    AutonomyDecision,
    AutonomyLifecycleEvent,
    AutonomyMode,
    AutonomyProfile,
    AutonomyProfileStatus,
    AutonomyRiskLevel,
    DelegationGrant,
    DelegationStatus,
    RunLevelRecord,
    RunLevelStatus,
)

autonomy_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_autonomy_profiles = Table(
    "aion_autonomy_profiles",
    autonomy_metadata,
    Column("autonomy_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("default_mode", Text, nullable=False),
    Column("max_mode", Text, nullable=False),
    Column("max_risk_level", Text, nullable=False),
    Column("allowed_action_types", json_payload_type, nullable=False),
    Column("denied_action_types", json_payload_type, nullable=False),
    Column("external_models_allowed", Boolean, nullable=False),
    Column("external_tools_allowed", Boolean, nullable=False),
    Column("background_workflows_allowed", Boolean, nullable=False),
    Column("scheduler_allowed", Boolean, nullable=False),
    Column("skill_promotion_allowed", Boolean, nullable=False),
    Column("memory_forgetting_allowed", Boolean, nullable=False),
    Column("approval_required_modes", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_autonomy_profiles_name", "name"),
    Index("ix_aion_autonomy_profiles_status", "status"),
    Index("ix_aion_autonomy_profiles_actor_id", "actor_id"),
    Index("ix_aion_autonomy_profiles_workspace_id", "workspace_id"),
    Index("ix_aion_autonomy_profiles_default_mode", "default_mode"),
    Index("ix_aion_autonomy_profiles_max_mode", "max_mode"),
    Index("ix_aion_autonomy_profiles_max_risk_level", "max_risk_level"),
    Index("ix_aion_autonomy_profiles_created_at", "created_at"),
)

aion_run_level_records = Table(
    "aion_run_level_records",
    autonomy_metadata,
    Column("run_level_id", Text, primary_key=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("active_profile_id", Text, nullable=True),
    Column("run_level", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("set_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("ended_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_run_level_records_actor_id", "actor_id"),
    Index("ix_aion_run_level_records_workspace_id", "workspace_id"),
    Index("ix_aion_run_level_records_active_profile_id", "active_profile_id"),
    Index("ix_aion_run_level_records_run_level", "run_level"),
    Index("ix_aion_run_level_records_status", "status"),
    Index("ix_aion_run_level_records_expires_at", "expires_at"),
    Index("ix_aion_run_level_records_created_at", "created_at"),
)

aion_delegation_grants = Table(
    "aion_delegation_grants",
    autonomy_metadata,
    Column("delegation_id", Text, primary_key=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("delegated_by", Text, nullable=True),
    Column("delegated_to", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("mode", Text, nullable=False),
    Column("max_risk_level", Text, nullable=False),
    Column("allowed_action_types", json_payload_type, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_delegation_grants_actor_id", "actor_id"),
    Index("ix_aion_delegation_grants_workspace_id", "workspace_id"),
    Index("ix_aion_delegation_grants_delegated_by", "delegated_by"),
    Index("ix_aion_delegation_grants_delegated_to", "delegated_to"),
    Index("ix_aion_delegation_grants_mode", "mode"),
    Index("ix_aion_delegation_grants_max_risk_level", "max_risk_level"),
    Index("ix_aion_delegation_grants_status", "status"),
    Index("ix_aion_delegation_grants_expires_at", "expires_at"),
    Index("ix_aion_delegation_grants_created_at", "created_at"),
)

aion_autonomy_decisions = Table(
    "aion_autonomy_decisions",
    autonomy_metadata,
    Column("autonomy_decision_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("requested_mode", Text, nullable=False),
    Column("resolved_mode", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("risk_level", Text, nullable=False),
    Column("allow", Boolean, nullable=False),
    Column("approval_required", Boolean, nullable=False),
    Column("delegation_id", Text, nullable=True),
    Column("autonomy_profile_id", Text, nullable=True),
    Column("run_level_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_autonomy_decisions_trace_id", "trace_id"),
    Index("ix_aion_autonomy_decisions_actor_id", "actor_id"),
    Index("ix_aion_autonomy_decisions_workspace_id", "workspace_id"),
    Index("ix_aion_autonomy_decisions_requested_mode", "requested_mode"),
    Index("ix_aion_autonomy_decisions_resolved_mode", "resolved_mode"),
    Index("ix_aion_autonomy_decisions_action_type", "action_type"),
    Index("ix_aion_autonomy_decisions_resource_type", "resource_type"),
    Index("ix_aion_autonomy_decisions_risk_level", "risk_level"),
    Index("ix_aion_autonomy_decisions_allow", "allow"),
    Index("ix_aion_autonomy_decisions_approval_required", "approval_required"),
    Index("ix_aion_autonomy_decisions_created_at", "created_at"),
)

aion_autonomy_lifecycle_events = Table(
    "aion_autonomy_lifecycle_events",
    autonomy_metadata,
    Column("autonomy_event_id", Text, primary_key=True),
    Column("autonomy_profile_id", Text, nullable=True),
    Column("run_level_id", Text, nullable=True),
    Column("delegation_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_autonomy_lifecycle_events_profile_id", "autonomy_profile_id"),
    Index("ix_aion_autonomy_lifecycle_events_run_level_id", "run_level_id"),
    Index("ix_aion_autonomy_lifecycle_events_delegation_id", "delegation_id"),
    Index("ix_aion_autonomy_lifecycle_events_decision_id", "autonomy_decision_id"),
    Index("ix_aion_autonomy_lifecycle_events_trace_id", "trace_id"),
    Index("ix_aion_autonomy_lifecycle_events_event_type", "event_type"),
    Index("ix_aion_autonomy_lifecycle_events_actor_id", "actor_id"),
    Index("ix_aion_autonomy_lifecycle_events_workspace_id", "workspace_id"),
    Index("ix_aion_autonomy_lifecycle_events_created_at", "created_at"),
)


class AutonomyRepository:
    """Repository for autonomy profiles, run levels, delegations, and decisions."""

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

    def save_profile(self, profile: AutonomyProfile) -> AutonomyProfile:
        """Upsert one autonomy profile."""
        self._ensure_schema()
        now = _now()
        stored = profile.model_copy(
            update={
                "created_at": profile.created_at or now,
                "updated_at": profile.updated_at or now,
            }
        )
        self._replace(aion_autonomy_profiles, "autonomy_profile_id", stored)
        return stored

    def get_profile(self, autonomy_profile_id: str) -> AutonomyProfile | None:
        """Return one autonomy profile."""
        row = self._get(aion_autonomy_profiles, "autonomy_profile_id", autonomy_profile_id)
        return _profile_from_row(row) if row is not None else None

    def list_profiles(
        self,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[AutonomyProfile]:
        """List autonomy profiles by optional filters."""
        self._ensure_schema()
        query = select(aion_autonomy_profiles)
        if actor_id is not None:
            query = query.where(aion_autonomy_profiles.c.actor_id == actor_id)
        if workspace_id is not None:
            query = query.where(aion_autonomy_profiles.c.workspace_id == workspace_id)
        if status is not None:
            query = query.where(aion_autonomy_profiles.c.status == status)
        query = query.order_by(aion_autonomy_profiles.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_profile_from_row(row) for row in rows]

    def get_active_profile(
        self,
        *,
        actor_id: str | None,
        workspace_id: str | None,
    ) -> AutonomyProfile | None:
        """Return the newest active matching profile."""
        profiles = self.list_profiles(actor_id=actor_id, workspace_id=workspace_id, status="active")
        if profiles:
            return profiles[0]
        profiles = self.list_profiles(actor_id=None, workspace_id=workspace_id, status="active")
        if profiles:
            return profiles[0]
        profiles = self.list_profiles(actor_id=actor_id, workspace_id=None, status="active")
        return profiles[0] if profiles else None

    def save_run_level(self, record: RunLevelRecord) -> RunLevelRecord:
        """Upsert one run-level record."""
        self._ensure_schema()
        stored = record.model_copy(update={"created_at": record.created_at or _now()})
        self._replace(aion_run_level_records, "run_level_id", stored)
        return stored

    def get_run_level(self, run_level_id: str) -> RunLevelRecord | None:
        """Return one run-level record."""
        row = self._get(aion_run_level_records, "run_level_id", run_level_id)
        return _run_level_from_row(row) if row is not None else None

    def list_run_levels(
        self,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[RunLevelRecord]:
        """List run-level records."""
        self._ensure_schema()
        query = select(aion_run_level_records)
        if actor_id is not None:
            query = query.where(aion_run_level_records.c.actor_id == actor_id)
        if workspace_id is not None:
            query = query.where(aion_run_level_records.c.workspace_id == workspace_id)
        if status is not None:
            query = query.where(aion_run_level_records.c.status == status)
        query = query.order_by(aion_run_level_records.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_run_level_from_row(row) for row in rows]

    def get_active_run_level(
        self,
        *,
        actor_id: str | None,
        workspace_id: str | None,
        now: datetime | None = None,
    ) -> RunLevelRecord | None:
        """Return the newest active non-expired run level."""
        current = now or _now()
        records = self.list_run_levels(
            actor_id=actor_id,
            workspace_id=workspace_id,
            status="active",
        )
        for record in records:
            if record.expires_at is None or _aware(record.expires_at) > current:
                return record
        return None

    def save_delegation(self, grant: DelegationGrant) -> DelegationGrant:
        """Upsert one delegation grant."""
        self._ensure_schema()
        stored = grant.model_copy(update={"created_at": grant.created_at or _now()})
        self._replace(aion_delegation_grants, "delegation_id", stored)
        return stored

    def get_delegation(self, delegation_id: str) -> DelegationGrant | None:
        """Return one delegation grant."""
        row = self._get(aion_delegation_grants, "delegation_id", delegation_id)
        return _delegation_from_row(row) if row is not None else None

    def list_delegations(
        self,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[DelegationGrant]:
        """List delegation grants."""
        self._ensure_schema()
        query = select(aion_delegation_grants)
        if actor_id is not None:
            query = query.where(aion_delegation_grants.c.actor_id == actor_id)
        if workspace_id is not None:
            query = query.where(aion_delegation_grants.c.workspace_id == workspace_id)
        if status is not None:
            query = query.where(aion_delegation_grants.c.status == status)
        query = query.order_by(aion_delegation_grants.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_delegation_from_row(row) for row in rows]

    def save_decision(self, decision: AutonomyDecision) -> AutonomyDecision:
        """Persist one autonomy decision."""
        self._ensure_schema()
        stored = decision.model_copy(update={"created_at": decision.created_at or _now()})
        self._replace(aion_autonomy_decisions, "autonomy_decision_id", stored)
        return stored

    def save_lifecycle_event(self, event: AutonomyLifecycleEvent) -> AutonomyLifecycleEvent:
        """Persist one autonomy lifecycle event."""
        self._ensure_schema()
        stored = event.model_copy(update={"created_at": event.created_at or _now()})
        self._replace(aion_autonomy_lifecycle_events, "autonomy_event_id", stored)
        return stored

    def _replace(self, table: Table, key: str, model: Any) -> None:
        with self._engine.begin() as connection:
            connection.execute(delete(table).where(table.c[key] == getattr(model, key)))
            connection.execute(insert(table).values(**model.model_dump(mode="python")))

    def _get(self, table: Table, key: str, value: str) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return connection.execute(select(table).where(table.c[key] == value)).mappings().first()

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        autonomy_metadata.create_all(self._engine)
        self._schema_ready = True


def _profile_from_row(row: RowMapping) -> AutonomyProfile:
    return AutonomyProfile(
        autonomy_profile_id=str(row["autonomy_profile_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(AutonomyProfileStatus, row["status"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_list_str(row["owner_scope"]),
        default_mode=cast(AutonomyMode, row["default_mode"]),
        max_mode=cast(AutonomyMode, row["max_mode"]),
        max_risk_level=cast(AutonomyRiskLevel, row["max_risk_level"]),
        allowed_action_types=_list_str(row["allowed_action_types"]),
        denied_action_types=_list_str(row["denied_action_types"]),
        external_models_allowed=bool(row["external_models_allowed"]),
        external_tools_allowed=bool(row["external_tools_allowed"]),
        background_workflows_allowed=bool(row["background_workflows_allowed"]),
        scheduler_allowed=bool(row["scheduler_allowed"]),
        skill_promotion_allowed=bool(row["skill_promotion_allowed"]),
        memory_forgetting_allowed=bool(row["memory_forgetting_allowed"]),
        approval_required_modes=[
            cast(AutonomyMode, mode) for mode in _list_str(row["approval_required_modes"])
        ],
        constraints=_list_str(row["constraints"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _run_level_from_row(row: RowMapping) -> RunLevelRecord:
    return RunLevelRecord(
        run_level_id=str(row["run_level_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        active_profile_id=_optional_str(row["active_profile_id"]),
        run_level=cast(AutonomyMode, row["run_level"]),
        status=cast(RunLevelStatus, row["status"]),
        reason=str(row["reason"]),
        constraints=_list_str(row["constraints"]),
        metadata=_dict(row["metadata"]),
        set_by=_optional_str(row["set_by"]),
        created_at=_optional_datetime(row["created_at"]),
        expires_at=_optional_datetime(row["expires_at"]),
        ended_at=_optional_datetime(row["ended_at"]),
    )


def _delegation_from_row(row: RowMapping) -> DelegationGrant:
    return DelegationGrant(
        delegation_id=str(row["delegation_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        delegated_by=_optional_str(row["delegated_by"]),
        delegated_to=_optional_str(row["delegated_to"]),
        owner_scope=_list_str(row["owner_scope"]),
        mode=cast(AutonomyMode, row["mode"]),
        max_risk_level=cast(AutonomyRiskLevel, row["max_risk_level"]),
        allowed_action_types=_list_str(row["allowed_action_types"]),
        resource_types=_list_str(row["resource_types"]),
        constraints=_list_str(row["constraints"]),
        status=cast(DelegationStatus, row["status"]),
        reason=str(row["reason"]),
        created_at=_optional_datetime(row["created_at"]),
        expires_at=_optional_datetime(row["expires_at"]),
        revoked_at=_optional_datetime(row["revoked_at"]),
    )


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _aware(value)
    return None


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _now() -> datetime:
    return datetime.now(UTC)
