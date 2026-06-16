"""Persistence for AION decision intelligence records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.counterfactuals import CounterfactualRun
from aion_brain.contracts.decisions import (
    DecisionFrame,
    DecisionOption,
    DecisionRecord,
    OptionEvaluation,
    TradeoffMatrix,
    UtilityProfile,
)

decision_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_decision_frames = Table(
    "aion_decision_frames",
    decision_metadata,
    Column("decision_frame_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("frame_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("question", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("situation_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("goal_refs", json_payload_type, nullable=False),
    Column("task_refs", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("assumptions", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_decision_frames_trace_id", "trace_id"),
    Index("ix_aion_decision_frames_actor_id", "actor_id"),
    Index("ix_aion_decision_frames_workspace_id", "workspace_id"),
    Index("ix_aion_decision_frames_status", "status"),
    Index("ix_aion_decision_frames_frame_type", "frame_type"),
    Index("ix_aion_decision_frames_created_at", "created_at"),
)

aion_decision_options = Table(
    "aion_decision_options",
    decision_metadata,
    Column("decision_option_id", Text, primary_key=True),
    Column(
        "decision_frame_id",
        Text,
        ForeignKey("aion_decision_frames.decision_frame_id"),
        nullable=False,
    ),
    Column("option_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("action_type", Text, nullable=True),
    Column("target_type", Text, nullable=True),
    Column("target_id", Text, nullable=True),
    Column("expected_effects", json_payload_type, nullable=False),
    Column("required_permissions", json_payload_type, nullable=False),
    Column("required_approvals", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("reversibility", Text, nullable=False),
    Column("cost_estimate", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_decision_options_frame", "decision_frame_id"),
    Index("ix_aion_decision_options_type", "option_type"),
    Index("ix_aion_decision_options_status", "status"),
    Index("ix_aion_decision_options_action_type", "action_type"),
    Index("ix_aion_decision_options_target_type", "target_type"),
    Index("ix_aion_decision_options_risk_level", "risk_level"),
    Index("ix_aion_decision_options_reversibility", "reversibility"),
    Index("ix_aion_decision_options_created_at", "created_at"),
)

aion_utility_profiles = Table(
    "aion_utility_profiles",
    decision_metadata,
    Column("utility_profile_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("weights", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("name", name="uq_aion_utility_profiles_name"),
    Index("ix_aion_utility_profiles_name", "name"),
    Index("ix_aion_utility_profiles_status", "status"),
    Index("ix_aion_utility_profiles_created_at", "created_at"),
)

aion_option_evaluations = Table(
    "aion_option_evaluations",
    decision_metadata,
    Column("option_evaluation_id", Text, primary_key=True),
    Column(
        "decision_frame_id",
        Text,
        ForeignKey("aion_decision_frames.decision_frame_id"),
        nullable=False,
    ),
    Column(
        "decision_option_id",
        Text,
        ForeignKey("aion_decision_options.decision_option_id"),
        nullable=False,
    ),
    Column("utility_profile_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("score", Float, nullable=False),
    Column("rank", Integer, nullable=True),
    Column("factors", json_payload_type, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("tradeoffs", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("explanation", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_option_evaluations_frame", "decision_frame_id"),
    Index("ix_aion_option_evaluations_option", "decision_option_id"),
    Index("ix_aion_option_evaluations_profile", "utility_profile_id"),
    Index("ix_aion_option_evaluations_status", "status"),
    Index("ix_aion_option_evaluations_score", "score"),
    Index("ix_aion_option_evaluations_rank", "rank"),
    Index("ix_aion_option_evaluations_created_at", "created_at"),
)

aion_tradeoff_matrices = Table(
    "aion_tradeoff_matrices",
    decision_metadata,
    Column("tradeoff_matrix_id", Text, primary_key=True),
    Column("decision_frame_id", Text, nullable=False),
    Column("utility_profile_id", Text, nullable=True),
    Column("option_ids", json_payload_type, nullable=False),
    Column("criteria", json_payload_type, nullable=False),
    Column("scores", json_payload_type, nullable=False),
    Column("recommended_option_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_tradeoff_matrices_frame", "decision_frame_id"),
    Index("ix_aion_tradeoff_matrices_profile", "utility_profile_id"),
    Index("ix_aion_tradeoff_matrices_recommended", "recommended_option_id"),
    Index("ix_aion_tradeoff_matrices_created_at", "created_at"),
)

aion_counterfactual_runs = Table(
    "aion_counterfactual_runs",
    decision_metadata,
    Column("counterfactual_run_id", Text, primary_key=True),
    Column("decision_frame_id", Text, nullable=False),
    Column("decision_option_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input_state", json_payload_type, nullable=False),
    Column("assumptions", json_payload_type, nullable=False),
    Column("projected_changes", json_payload_type, nullable=False),
    Column("projected_risks", json_payload_type, nullable=False),
    Column("unknowns", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_counterfactual_runs_frame", "decision_frame_id"),
    Index("ix_aion_counterfactual_runs_option", "decision_option_id"),
    Index("ix_aion_counterfactual_runs_trace_id", "trace_id"),
    Index("ix_aion_counterfactual_runs_status", "status"),
    Index("ix_aion_counterfactual_runs_mode", "mode"),
    Index("ix_aion_counterfactual_runs_score", "score"),
    Index("ix_aion_counterfactual_runs_created_at", "created_at"),
)

aion_decision_journal_records = Table(
    "aion_decision_journal_records",
    decision_metadata,
    Column("decision_record_id", Text, primary_key=True),
    Column("decision_frame_id", Text, nullable=False),
    Column("selected_option_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("decision_type", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("evaluation_refs", json_payload_type, nullable=False),
    Column("counterfactual_refs", json_payload_type, nullable=False),
    Column("approval_request_id", Text, nullable=True),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("outcome_ref", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("superseded_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_decision_records_frame", "decision_frame_id"),
    Index("ix_aion_decision_records_selected", "selected_option_id"),
    Index("ix_aion_decision_records_trace_id", "trace_id"),
    Index("ix_aion_decision_records_actor_id", "actor_id"),
    Index("ix_aion_decision_records_workspace_id", "workspace_id"),
    Index("ix_aion_decision_records_status", "status"),
    Index("ix_aion_decision_records_type", "decision_type"),
    Index("ix_aion_decision_records_created_at", "created_at"),
)


class DecisionRepository:
    """Repository for decision frames, options, evaluations, and journals."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        url = database_url or "sqlite+pysqlite:///:memory:"
        self._engine = engine or create_engine(
            url,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
            poolclass=StaticPool if url.startswith("sqlite") else QueuePool,
            pool_pre_ping=not url.startswith("sqlite"),
        )
        self._auto_create = auto_create
        self._schema_ready = False

    def save_frame(self, frame: DecisionFrame) -> DecisionFrame:
        self._upsert(aion_decision_frames, "decision_frame_id", frame.model_dump(mode="python"))
        return frame

    def get_frame(self, decision_frame_id: str) -> DecisionFrame | None:
        row = self._first(
            select(aion_decision_frames).where(
                aion_decision_frames.c.decision_frame_id == decision_frame_id
            )
        )
        return DecisionFrame(**dict(row)) if row is not None else None

    def list_frames(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        frame_type: str | None = None,
        limit: int = 50,
    ) -> list[DecisionFrame]:
        statement = select(aion_decision_frames).order_by(aion_decision_frames.c.created_at.desc())
        if status:
            statement = statement.where(aion_decision_frames.c.status == status)
        if frame_type:
            statement = statement.where(aion_decision_frames.c.frame_type == frame_type)
        frames: list[DecisionFrame] = []
        for row in self._all(statement):
            frame = DecisionFrame(**dict(row))
            if not _scope_matches(frame.owner_scope, scope):
                continue
            frames.append(frame)
            if len(frames) >= limit:
                break
        return frames

    def save_option(self, option: DecisionOption) -> DecisionOption:
        self._upsert(
            aion_decision_options,
            "decision_option_id",
            option.model_dump(mode="python"),
        )
        return option

    def get_option(self, decision_option_id: str) -> DecisionOption | None:
        row = self._first(
            select(aion_decision_options).where(
                aion_decision_options.c.decision_option_id == decision_option_id
            )
        )
        return DecisionOption(**dict(row)) if row is not None else None

    def list_options(
        self,
        decision_frame_id: str,
        *,
        status: str | None = None,
    ) -> list[DecisionOption]:
        statement = (
            select(aion_decision_options)
            .where(aion_decision_options.c.decision_frame_id == decision_frame_id)
            .order_by(aion_decision_options.c.created_at.asc())
        )
        if status:
            statement = statement.where(aion_decision_options.c.status == status)
        return [DecisionOption(**dict(row)) for row in self._all(statement)]

    def save_profile(self, profile: UtilityProfile) -> UtilityProfile:
        self._upsert(aion_utility_profiles, "utility_profile_id", profile.model_dump(mode="python"))
        return profile

    def get_profile(self, name_or_id: str) -> UtilityProfile | None:
        row = self._first(
            select(aion_utility_profiles).where(
                (aion_utility_profiles.c.utility_profile_id == name_or_id)
                | (aion_utility_profiles.c.name == name_or_id)
            )
        )
        return UtilityProfile(**dict(row)) if row is not None else None

    def list_profiles(
        self,
        *,
        scope: list[str],
        status: str | None = None,
    ) -> list[UtilityProfile]:
        statement = select(aion_utility_profiles).order_by(
            aion_utility_profiles.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_utility_profiles.c.status == status)
        profiles: list[UtilityProfile] = []
        for row in self._all(statement):
            profile = UtilityProfile(**dict(row))
            if not _scope_matches(profile.owner_scope, scope):
                continue
            profiles.append(profile)
        return profiles

    def save_evaluation(self, evaluation: OptionEvaluation) -> OptionEvaluation:
        self._upsert(
            aion_option_evaluations,
            "option_evaluation_id",
            evaluation.model_dump(mode="python"),
        )
        return evaluation

    def list_evaluations(
        self,
        decision_frame_id: str,
        *,
        option_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[OptionEvaluation]:
        statement = (
            select(aion_option_evaluations)
            .where(aion_option_evaluations.c.decision_frame_id == decision_frame_id)
            .order_by(aion_option_evaluations.c.rank.asc(), aion_option_evaluations.c.score.desc())
        )
        if option_ids:
            statement = statement.where(
                aion_option_evaluations.c.decision_option_id.in_(option_ids)
            )
        return [OptionEvaluation(**dict(row)) for row in self._all(statement)[:limit]]

    def save_tradeoff_matrix(self, matrix: TradeoffMatrix) -> TradeoffMatrix:
        self._upsert(
            aion_tradeoff_matrices,
            "tradeoff_matrix_id",
            matrix.model_dump(mode="python"),
        )
        return matrix

    def save_counterfactual(self, run: CounterfactualRun) -> CounterfactualRun:
        self._upsert(
            aion_counterfactual_runs,
            "counterfactual_run_id",
            run.model_dump(mode="python"),
        )
        return run

    def get_counterfactual(self, counterfactual_run_id: str) -> CounterfactualRun | None:
        row = self._first(
            select(aion_counterfactual_runs).where(
                aion_counterfactual_runs.c.counterfactual_run_id == counterfactual_run_id
            )
        )
        return CounterfactualRun(**dict(row)) if row is not None else None

    def list_counterfactuals(
        self,
        decision_frame_id: str,
        *,
        limit: int = 100,
    ) -> list[CounterfactualRun]:
        statement = (
            select(aion_counterfactual_runs)
            .where(aion_counterfactual_runs.c.decision_frame_id == decision_frame_id)
            .order_by(aion_counterfactual_runs.c.created_at.desc())
        )
        return [CounterfactualRun(**dict(row)) for row in self._all(statement)[:limit]]

    def list_counterfactual_runs(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[CounterfactualRun]:
        statement = select(aion_counterfactual_runs).order_by(
            aion_counterfactual_runs.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_counterfactual_runs.c.status == status)
        return [CounterfactualRun(**dict(row)) for row in self._all(statement)[:limit]]

    def save_record(self, record: DecisionRecord) -> DecisionRecord:
        self._upsert(
            aion_decision_journal_records,
            "decision_record_id",
            record.model_dump(mode="python"),
        )
        return record

    def get_record(self, decision_record_id: str) -> DecisionRecord | None:
        row = self._first(
            select(aion_decision_journal_records).where(
                aion_decision_journal_records.c.decision_record_id == decision_record_id
            )
        )
        return DecisionRecord(**dict(row)) if row is not None else None

    def list_records(
        self,
        *,
        scope: list[str],
        decision_frame_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[DecisionRecord]:
        statement = select(aion_decision_journal_records).order_by(
            aion_decision_journal_records.c.created_at.desc()
        )
        if decision_frame_id:
            statement = statement.where(
                aion_decision_journal_records.c.decision_frame_id == decision_frame_id
            )
        if status:
            statement = statement.where(aion_decision_journal_records.c.status == status)
        records: list[DecisionRecord] = []
        for row in self._all(statement):
            record = DecisionRecord(**dict(row))
            frame = self.get_frame(record.decision_frame_id)
            if frame is not None and not _scope_matches(frame.owner_scope, scope):
                continue
            records.append(record)
            if len(records) >= limit:
                break
        return records

    def _upsert(self, table: Table, key: str, values: dict[str, Any]) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key]).where(table.c[key] == values[key])
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key] == values[key]).values(**values)
                )

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            decision_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return connection.execute(statement).mappings().first()

    def _all(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return list(connection.execute(statement).mappings().all())


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))


def now_utc() -> datetime:
    """Return current UTC time for decision services."""
    return datetime.now(UTC)


__all__ = [
    "DecisionRepository",
    "aion_counterfactual_runs",
    "aion_decision_frames",
    "aion_decision_journal_records",
    "aion_decision_options",
    "aion_option_evaluations",
    "aion_tradeoff_matrices",
    "aion_utility_profiles",
    "decision_metadata",
    "now_utc",
]
