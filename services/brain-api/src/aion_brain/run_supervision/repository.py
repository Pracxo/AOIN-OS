"""Persistent repository for run supervision records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.types import JSON

from aion_brain.contracts.compensation import CompensationPlan, CompensationStep
from aion_brain.contracts.run_control import RunControlRequest
from aion_brain.contracts.run_supervision import (
    RunStatusSample,
    RunSupervisionRecord,
    RunSupervisionReport,
    RunTimeoutPolicy,
)

run_supervision_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_run_supervision_records = Table(
    "aion_run_supervision_records",
    run_supervision_metadata,
    Column("run_supervision_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("target_system", Text, nullable=False),
    Column("target_run_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("run_type", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("current_status", Text, nullable=False),
    Column("previous_status", Text, nullable=True),
    Column("timeout_policy_id", Text, nullable=True),
    Column("deadline_at", DateTime(timezone=True), nullable=True),
    Column("last_sample_id", Text, nullable=True),
    Column("last_seen_at", DateTime(timezone=True), nullable=True),
    Column("stalled", Boolean, nullable=False),
    Column("cancellable", Boolean, nullable=False),
    Column("pausable", Boolean, nullable=False),
    Column("resumable", Boolean, nullable=False),
    Column("compensation_available", Boolean, nullable=False),
    Column("outcome_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_run_supervisions_trace_id", "trace_id"),
    Index("ix_aion_run_supervisions_actor_id", "actor_id"),
    Index("ix_aion_run_supervisions_workspace_id", "workspace_id"),
    Index("ix_aion_run_supervisions_source_type", "source_type"),
    Index("ix_aion_run_supervisions_source_id", "source_id"),
    Index("ix_aion_run_supervisions_target_system", "target_system"),
    Index("ix_aion_run_supervisions_target_run_id", "target_run_id"),
    Index("ix_aion_run_supervisions_status", "status"),
    Index("ix_aion_run_supervisions_run_type", "run_type"),
    Index("ix_aion_run_supervisions_current_status", "current_status"),
    Index("ix_aion_run_supervisions_stalled", "stalled"),
    Index("ix_aion_run_supervisions_deadline_at", "deadline_at"),
    Index("ix_aion_run_supervisions_last_seen_at", "last_seen_at"),
    Index("ix_aion_run_supervisions_created_at", "created_at"),
    Index("ix_aion_run_supervisions_deleted_at", "deleted_at"),
)

aion_run_status_samples = Table(
    "aion_run_status_samples",
    run_supervision_metadata,
    Column("run_status_sample_id", Text, primary_key=True),
    Column(
        "run_supervision_id",
        Text,
        ForeignKey("aion_run_supervision_records.run_supervision_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("target_system", Text, nullable=False),
    Column("target_run_id", Text, nullable=True),
    Column("observed_status", Text, nullable=False),
    Column("raw_status", json_payload_type, nullable=False),
    Column("progress", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_run_samples_run_supervision_id", "run_supervision_id"),
    Index("ix_aion_run_samples_trace_id", "trace_id"),
    Index("ix_aion_run_samples_target_system", "target_system"),
    Index("ix_aion_run_samples_target_run_id", "target_run_id"),
    Index("ix_aion_run_samples_observed_status", "observed_status"),
    Index("ix_aion_run_samples_observed_at", "observed_at"),
)

aion_run_control_requests = Table(
    "aion_run_control_requests",
    run_supervision_metadata,
    Column("run_control_request_id", Text, primary_key=True),
    Column(
        "run_supervision_id",
        Text,
        ForeignKey("aion_run_supervision_records.run_supervision_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("control_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("requested_mode", Text, nullable=False),
    Column("target_system", Text, nullable=False),
    Column("target_run_id", Text, nullable=True),
    Column("policy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("blocker_refs", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_run_controls_run_supervision_id", "run_supervision_id"),
    Index("ix_aion_run_controls_trace_id", "trace_id"),
    Index("ix_aion_run_controls_actor_id", "actor_id"),
    Index("ix_aion_run_controls_workspace_id", "workspace_id"),
    Index("ix_aion_run_controls_control_type", "control_type"),
    Index("ix_aion_run_controls_status", "status"),
    Index("ix_aion_run_controls_requested_mode", "requested_mode"),
    Index("ix_aion_run_controls_target_system", "target_system"),
    Index("ix_aion_run_controls_target_run_id", "target_run_id"),
    Index("ix_aion_run_controls_created_at", "created_at"),
)

aion_run_timeout_policies = Table(
    "aion_run_timeout_policies",
    run_supervision_metadata,
    Column("timeout_policy_id", Text, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("target_system", Text, nullable=False),
    Column("run_type", Text, nullable=False),
    Column("timeout_seconds", Integer, nullable=False),
    Column("stall_after_seconds", Integer, nullable=False),
    Column("max_status_age_seconds", Integer, nullable=False),
    Column("severity", Text, nullable=False),
    Column("action_on_timeout", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_run_timeout_policies_name", "name"),
    Index("ix_aion_run_timeout_policies_status", "status"),
    Index("ix_aion_run_timeout_policies_target_system", "target_system"),
    Index("ix_aion_run_timeout_policies_run_type", "run_type"),
    Index("ix_aion_run_timeout_policies_severity", "severity"),
    Index("ix_aion_run_timeout_policies_action_on_timeout", "action_on_timeout"),
    Index("ix_aion_run_timeout_policies_created_at", "created_at"),
)

aion_compensation_plans = Table(
    "aion_compensation_plans",
    run_supervision_metadata,
    Column("compensation_plan_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("run_supervision_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("plan_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("trigger_reason", Text, nullable=False),
    Column("target_refs", json_payload_type, nullable=False),
    Column("step_ids", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("approval_request_id", Text, nullable=True),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("executable", Boolean, nullable=False),
    Column("execution_allowed", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("approved_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_compensation_plans_trace_id", "trace_id"),
    Index("ix_aion_compensation_plans_run_supervision_id", "run_supervision_id"),
    Index("ix_aion_compensation_plans_source_type", "source_type"),
    Index("ix_aion_compensation_plans_source_id", "source_id"),
    Index("ix_aion_compensation_plans_status", "status"),
    Index("ix_aion_compensation_plans_plan_type", "plan_type"),
    Index("ix_aion_compensation_plans_risk_level", "risk_level"),
    Index("ix_aion_compensation_plans_executable", "executable"),
    Index("ix_aion_compensation_plans_execution_allowed", "execution_allowed"),
    Index("ix_aion_compensation_plans_created_at", "created_at"),
    Index("ix_aion_compensation_plans_deleted_at", "deleted_at"),
)

aion_compensation_steps = Table(
    "aion_compensation_steps",
    run_supervision_metadata,
    Column("compensation_step_id", Text, primary_key=True),
    Column(
        "compensation_plan_id",
        Text,
        ForeignKey("aion_compensation_plans.compensation_plan_id"),
        nullable=False,
    ),
    Column("step_order", Integer, nullable=False),
    Column("step_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("proposed_action_type", Text, nullable=True),
    Column("proposed_target_system", Text, nullable=True),
    Column("proposed_payload", json_payload_type, nullable=False),
    Column("expected_effects", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("requires_approval", Boolean, nullable=False),
    Column("action_proposal_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_compensation_steps_plan_id", "compensation_plan_id"),
    Index("ix_aion_compensation_steps_step_order", "step_order"),
    Index("ix_aion_compensation_steps_step_type", "step_type"),
    Index("ix_aion_compensation_steps_status", "status"),
    Index("ix_aion_compensation_steps_proposed_action_type", "proposed_action_type"),
    Index("ix_aion_compensation_steps_proposed_target_system", "proposed_target_system"),
    Index("ix_aion_compensation_steps_risk_level", "risk_level"),
    Index("ix_aion_compensation_steps_requires_approval", "requires_approval"),
    Index("ix_aion_compensation_steps_created_at", "created_at"),
)

aion_run_supervision_reports = Table(
    "aion_run_supervision_reports",
    run_supervision_metadata,
    Column("supervision_report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("target_systems", json_payload_type, nullable=False),
    Column("run_count", Integer, nullable=False),
    Column("active_count", Integer, nullable=False),
    Column("completed_count", Integer, nullable=False),
    Column("failed_count", Integer, nullable=False),
    Column("stalled_count", Integer, nullable=False),
    Column("timeout_count", Integer, nullable=False),
    Column("control_request_count", Integer, nullable=False),
    Column("compensation_plan_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_run_supervision_reports_trace_id", "trace_id"),
    Index("ix_aion_run_supervision_reports_status", "status"),
    Index("ix_aion_run_supervision_reports_run_count", "run_count"),
    Index("ix_aion_run_supervision_reports_stalled_count", "stalled_count"),
    Index("ix_aion_run_supervision_reports_timeout_count", "timeout_count"),
    Index("ix_aion_run_supervision_reports_created_at", "created_at"),
)


class RunSupervisionRepository:
    """Repository for run supervision, control, timeout, and compensation records."""

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

    def save_run(self, run: RunSupervisionRecord) -> RunSupervisionRecord:
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "updated_at": run.updated_at or datetime.now(UTC),
            }
        )
        self._upsert(aion_run_supervision_records, "run_supervision_id", stored)
        return stored

    def get_run(self, run_supervision_id: str) -> RunSupervisionRecord | None:
        row = self._get(aion_run_supervision_records, "run_supervision_id", run_supervision_id)
        return RunSupervisionRecord(**row) if row is not None else None

    def list_runs(
        self,
        *,
        scope: list[str],
        target_system: str | None = None,
        status: str | None = None,
        stalled: bool | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[RunSupervisionRecord]:
        self._ensure_schema()
        statement = select(aion_run_supervision_records).order_by(
            aion_run_supervision_records.c.created_at.desc()
        )
        if target_system is not None:
            statement = statement.where(
                aion_run_supervision_records.c.target_system == target_system
            )
        if status is not None:
            statement = statement.where(aion_run_supervision_records.c.status == status)
        if stalled is not None:
            statement = statement.where(aion_run_supervision_records.c.stalled == stalled)
        if not include_deleted:
            statement = statement.where(aion_run_supervision_records.c.deleted_at.is_(None))
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            RunSupervisionRecord(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_sample(self, sample: RunStatusSample) -> RunStatusSample:
        stored = sample.model_copy(update={"observed_at": sample.observed_at or datetime.now(UTC)})
        self._upsert(aion_run_status_samples, "run_status_sample_id", stored)
        return stored

    def list_samples(
        self, run_supervision_id: str | None = None, limit: int = 100
    ) -> list[RunStatusSample]:
        self._ensure_schema()
        statement = select(aion_run_status_samples).order_by(
            aion_run_status_samples.c.observed_at.desc()
        )
        if run_supervision_id is not None:
            statement = statement.where(
                aion_run_status_samples.c.run_supervision_id == run_supervision_id
            )
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [RunStatusSample(**dict(row)) for row in rows]

    def save_control_request(self, request: RunControlRequest) -> RunControlRequest:
        stored = request.model_copy(update={"created_at": request.created_at or datetime.now(UTC)})
        self._upsert(aion_run_control_requests, "run_control_request_id", stored)
        return stored

    def get_control_request(self, run_control_request_id: str) -> RunControlRequest | None:
        row = self._get(
            aion_run_control_requests,
            "run_control_request_id",
            run_control_request_id,
        )
        return RunControlRequest(**row) if row is not None else None

    def list_control_requests(
        self,
        *,
        run_supervision_id: str | None = None,
        status: str | None = None,
        control_type: str | None = None,
        limit: int = 100,
    ) -> list[RunControlRequest]:
        self._ensure_schema()
        statement = select(aion_run_control_requests).order_by(
            aion_run_control_requests.c.created_at.desc()
        )
        if run_supervision_id is not None:
            statement = statement.where(
                aion_run_control_requests.c.run_supervision_id == run_supervision_id
            )
        if status is not None:
            statement = statement.where(aion_run_control_requests.c.status == status)
        if control_type is not None:
            statement = statement.where(aion_run_control_requests.c.control_type == control_type)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [RunControlRequest(**dict(row)) for row in rows]

    def save_timeout_policy(self, policy: RunTimeoutPolicy) -> RunTimeoutPolicy:
        stored = policy.model_copy(
            update={
                "created_at": policy.created_at or datetime.now(UTC),
                "updated_at": policy.updated_at or datetime.now(UTC),
            }
        )
        self._upsert(aion_run_timeout_policies, "timeout_policy_id", stored)
        return stored

    def get_timeout_policy(self, timeout_policy_id: str) -> RunTimeoutPolicy | None:
        row = self._get(aion_run_timeout_policies, "timeout_policy_id", timeout_policy_id)
        return RunTimeoutPolicy(**row) if row is not None else None

    def list_timeout_policies(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        target_system: str | None = None,
        run_type: str | None = None,
    ) -> list[RunTimeoutPolicy]:
        self._ensure_schema()
        statement = select(aion_run_timeout_policies).order_by(
            aion_run_timeout_policies.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_run_timeout_policies.c.status == status)
        if target_system is not None:
            statement = statement.where(aion_run_timeout_policies.c.target_system == target_system)
        if run_type is not None:
            statement = statement.where(aion_run_timeout_policies.c.run_type == run_type)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            RunTimeoutPolicy(**dict(row))
            for row in rows
            if _scope_matches(row["owner_scope"], scope)
        ]

    def save_compensation_plan(self, plan: CompensationPlan) -> CompensationPlan:
        stored = plan.model_copy(update={"created_at": plan.created_at or datetime.now(UTC)})
        self._ensure_schema()
        plan_values = stored.model_dump(mode="python", exclude={"steps"})
        plan_values["step_ids"] = [step.compensation_step_id for step in stored.steps]
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_compensation_plans.c.compensation_plan_id).where(
                    aion_compensation_plans.c.compensation_plan_id == stored.compensation_plan_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_compensation_plans).values(**plan_values))
            else:
                connection.execute(
                    update(aion_compensation_plans)
                    .where(
                        aion_compensation_plans.c.compensation_plan_id
                        == stored.compensation_plan_id
                    )
                    .values(**plan_values)
                )
            for step in stored.steps:
                step_values = step.model_dump(mode="python")
                existing_step = connection.execute(
                    select(aion_compensation_steps.c.compensation_step_id).where(
                        aion_compensation_steps.c.compensation_step_id == step.compensation_step_id
                    )
                ).first()
                if existing_step is None:
                    connection.execute(insert(aion_compensation_steps).values(**step_values))
                else:
                    connection.execute(
                        update(aion_compensation_steps)
                        .where(
                            aion_compensation_steps.c.compensation_step_id
                            == step.compensation_step_id
                        )
                        .values(**step_values)
                    )
        return stored

    def get_compensation_plan(self, compensation_plan_id: str) -> CompensationPlan | None:
        row = self._get(aion_compensation_plans, "compensation_plan_id", compensation_plan_id)
        if row is None:
            return None
        steps = self.list_compensation_steps(compensation_plan_id)
        row.pop("step_ids", None)
        return CompensationPlan(**row, steps=steps)

    def list_compensation_plans(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        run_supervision_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[CompensationPlan]:
        self._ensure_schema()
        statement = select(aion_compensation_plans).order_by(
            aion_compensation_plans.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_compensation_plans.c.status == status)
        if run_supervision_id is not None:
            statement = statement.where(
                aion_compensation_plans.c.run_supervision_id == run_supervision_id
            )
        if not include_deleted:
            statement = statement.where(aion_compensation_plans.c.deleted_at.is_(None))
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        plans: list[CompensationPlan] = []
        for row in rows:
            row_dict = dict(row)
            if not _scope_matches(row_dict["owner_scope"], scope):
                continue
            row_dict.pop("step_ids", None)
            plans.append(
                CompensationPlan(
                    **row_dict,
                    steps=self.list_compensation_steps(str(row_dict["compensation_plan_id"])),
                )
            )
        return plans

    def list_compensation_steps(self, compensation_plan_id: str) -> list[CompensationStep]:
        self._ensure_schema()
        statement = (
            select(aion_compensation_steps)
            .where(aion_compensation_steps.c.compensation_plan_id == compensation_plan_id)
            .order_by(aion_compensation_steps.c.step_order.asc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [CompensationStep(**dict(row)) for row in rows]

    def save_report(self, report: RunSupervisionReport) -> RunSupervisionReport:
        stored = report.model_copy(update={"created_at": report.created_at or datetime.now(UTC)})
        self._upsert(aion_run_supervision_reports, "supervision_report_id", stored)
        return stored

    def list_reports(self, limit: int = 100) -> list[RunSupervisionReport]:
        self._ensure_schema()
        statement = (
            select(aion_run_supervision_reports)
            .order_by(aion_run_supervision_reports.c.created_at.desc())
            .limit(limit)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [RunSupervisionReport(**dict(row)) for row in rows]

    def _upsert(self, table: Table, id_column: str, model: object) -> None:
        self._ensure_schema()
        values = model.model_dump(mode="python")  # type: ignore[attr-defined]
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(getattr(table.c, id_column)).where(
                    getattr(table.c, id_column) == values[id_column]
                )
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table)
                    .where(getattr(table.c, id_column) == values[id_column])
                    .values(**values)
                )

    def _get(self, table: Table, id_column: str, value: str) -> dict[str, Any] | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(getattr(table.c, id_column) == value))
                .mappings()
                .first()
            )
        return dict(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            run_supervision_metadata.create_all(self._engine)
        self._schema_ready = True


def _scope_matches(owner_scope: object, query_scope: list[str]) -> bool:
    if not isinstance(owner_scope, list):
        return True
    return bool(set(str(item) for item in owner_scope).intersection(query_scope))


__all__ = ["RunSupervisionRepository"]
