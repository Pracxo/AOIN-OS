"""Persistence for AION outcome ledger records."""

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

from aion_brain.contracts.effects import ExpectedEffect, ObservedEffect
from aion_brain.contracts.outcomes import (
    CausalAttribution,
    EffectVerificationRun,
    OutcomeFeedback,
    OutcomeQuery,
    OutcomeRecord,
)

outcome_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_outcome_records = Table(
    "aion_outcome_records",
    outcome_metadata,
    Column("outcome_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("outcome_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("expected_effects", json_payload_type, nullable=False),
    Column("observed_effects", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("situation_refs", json_payload_type, nullable=False),
    Column("decision_refs", json_payload_type, nullable=False),
    Column("execution_refs", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("score", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_outcome_records_trace_id", "trace_id"),
    Index("ix_aion_outcome_records_actor_id", "actor_id"),
    Index("ix_aion_outcome_records_workspace_id", "workspace_id"),
    Index("ix_aion_outcome_records_source_type", "source_type"),
    Index("ix_aion_outcome_records_source_id", "source_id"),
    Index("ix_aion_outcome_records_status", "status"),
    Index("ix_aion_outcome_records_outcome_type", "outcome_type"),
    Index("ix_aion_outcome_records_confidence", "confidence"),
    Index("ix_aion_outcome_records_score", "score"),
    Index("ix_aion_outcome_records_observed_at", "observed_at"),
    Index("ix_aion_outcome_records_created_at", "created_at"),
    Index("ix_aion_outcome_records_deleted_at", "deleted_at"),
)

aion_expected_effects = Table(
    "aion_expected_effects",
    outcome_metadata,
    Column("expected_effect_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("effect_type", Text, nullable=False),
    Column("subject_ref", Text, nullable=True),
    Column("predicate", Text, nullable=False),
    Column("object_ref", Text, nullable=True),
    Column("expected_value", json_payload_type, nullable=False),
    Column("success_criteria", json_payload_type, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_expected_effects_trace_id", "trace_id"),
    Index("ix_aion_expected_effects_source_type", "source_type"),
    Index("ix_aion_expected_effects_source_id", "source_id"),
    Index("ix_aion_expected_effects_effect_type", "effect_type"),
    Index("ix_aion_expected_effects_subject_ref", "subject_ref"),
    Index("ix_aion_expected_effects_predicate", "predicate"),
    Index("ix_aion_expected_effects_object_ref", "object_ref"),
    Index("ix_aion_expected_effects_required", "required"),
    Index("ix_aion_expected_effects_confidence", "confidence"),
    Index("ix_aion_expected_effects_deleted_at", "deleted_at"),
    Index("ix_aion_expected_effects_created_at", "created_at"),
)

aion_observed_effects = Table(
    "aion_observed_effects",
    outcome_metadata,
    Column("observed_effect_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("outcome_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("effect_type", Text, nullable=False),
    Column("subject_ref", Text, nullable=True),
    Column("predicate", Text, nullable=False),
    Column("object_ref", Text, nullable=True),
    Column("observed_value", json_payload_type, nullable=False),
    Column("observation_source_type", Text, nullable=False),
    Column("observation_source_id", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("situation_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_observed_effects_trace_id", "trace_id"),
    Index("ix_aion_observed_effects_outcome_id", "outcome_id"),
    Index("ix_aion_observed_effects_source_type", "source_type"),
    Index("ix_aion_observed_effects_source_id", "source_id"),
    Index("ix_aion_observed_effects_effect_type", "effect_type"),
    Index("ix_aion_observed_effects_subject_ref", "subject_ref"),
    Index("ix_aion_observed_effects_predicate", "predicate"),
    Index("ix_aion_observed_effects_object_ref", "object_ref"),
    Index("ix_aion_observed_effects_observation_source_type", "observation_source_type"),
    Index("ix_aion_observed_effects_observation_source_id", "observation_source_id"),
    Index("ix_aion_observed_effects_confidence", "confidence"),
    Index("ix_aion_observed_effects_sensitivity", "sensitivity"),
    Index("ix_aion_observed_effects_observed_at", "observed_at"),
    Index("ix_aion_observed_effects_deleted_at", "deleted_at"),
    Index("ix_aion_observed_effects_created_at", "created_at"),
)

aion_effect_verification_runs = Table(
    "aion_effect_verification_runs",
    outcome_metadata,
    Column("verification_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("outcome_id", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("expected_effect_ids", json_payload_type, nullable=False),
    Column("observed_effect_ids", json_payload_type, nullable=False),
    Column("matched_effects", json_payload_type, nullable=False),
    Column("missing_effects", json_payload_type, nullable=False),
    Column("unexpected_effects", json_payload_type, nullable=False),
    Column("contradicted_effects", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_effect_verification_runs_trace_id", "trace_id"),
    Index("ix_aion_effect_verification_runs_outcome_id", "outcome_id"),
    Index("ix_aion_effect_verification_runs_source_type", "source_type"),
    Index("ix_aion_effect_verification_runs_source_id", "source_id"),
    Index("ix_aion_effect_verification_runs_status", "status"),
    Index("ix_aion_effect_verification_runs_mode", "mode"),
    Index("ix_aion_effect_verification_runs_score", "score"),
    Index("ix_aion_effect_verification_runs_created_at", "created_at"),
)

aion_causal_attributions = Table(
    "aion_causal_attributions",
    outcome_metadata,
    Column("causal_attribution_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("outcome_id", Text, nullable=False),
    Column("cause_type", Text, nullable=False),
    Column("cause_id", Text, nullable=False),
    Column("effect_type", Text, nullable=False),
    Column("effect_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("reasoning", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_causal_attributions_trace_id", "trace_id"),
    Index("ix_aion_causal_attributions_outcome_id", "outcome_id"),
    Index("ix_aion_causal_attributions_cause_type", "cause_type"),
    Index("ix_aion_causal_attributions_cause_id", "cause_id"),
    Index("ix_aion_causal_attributions_effect_type", "effect_type"),
    Index("ix_aion_causal_attributions_effect_id", "effect_id"),
    Index("ix_aion_causal_attributions_relation_type", "relation_type"),
    Index("ix_aion_causal_attributions_confidence", "confidence"),
    Index("ix_aion_causal_attributions_deleted_at", "deleted_at"),
    Index("ix_aion_causal_attributions_created_at", "created_at"),
)

aion_outcome_feedback_records = Table(
    "aion_outcome_feedback_records",
    outcome_metadata,
    Column("outcome_feedback_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("outcome_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("feedback_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("message", Text, nullable=False),
    Column("recommended_followup", Text, nullable=False),
    Column("learning_signal_id", Text, nullable=True),
    Column("reflection_id", Text, nullable=True),
    Column("regression_case_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_outcome_feedback_trace_id", "trace_id"),
    Index("ix_aion_outcome_feedback_outcome_id", "outcome_id"),
    Index("ix_aion_outcome_feedback_source_type", "source_type"),
    Index("ix_aion_outcome_feedback_source_id", "source_id"),
    Index("ix_aion_outcome_feedback_feedback_type", "feedback_type"),
    Index("ix_aion_outcome_feedback_status", "status"),
    Index("ix_aion_outcome_feedback_severity", "severity"),
    Index("ix_aion_outcome_feedback_learning_signal_id", "learning_signal_id"),
    Index("ix_aion_outcome_feedback_reflection_id", "reflection_id"),
    Index("ix_aion_outcome_feedback_regression_case_id", "regression_case_id"),
    Index("ix_aion_outcome_feedback_created_at", "created_at"),
)


class OutcomeRepository:
    """Repository for outcome records, effects, verification, attribution, and feedback."""

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

    def save_expected_effect(self, effect: ExpectedEffect) -> ExpectedEffect:
        self._upsert(
            aion_expected_effects,
            "expected_effect_id",
            effect.model_dump(mode="python"),
        )
        return effect

    def get_expected_effect(self, expected_effect_id: str) -> ExpectedEffect | None:
        row = self._first(
            select(aion_expected_effects).where(
                aion_expected_effects.c.expected_effect_id == expected_effect_id
            )
        )
        return ExpectedEffect(**dict(row)) if row is not None else None

    def list_expected_effects(
        self,
        *,
        source_type: str | None = None,
        source_id: str | None = None,
        trace_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ExpectedEffect]:
        statement = select(aion_expected_effects).order_by(
            aion_expected_effects.c.created_at.desc()
        )
        if source_type:
            statement = statement.where(aion_expected_effects.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_expected_effects.c.source_id == source_id)
        if trace_id:
            statement = statement.where(aion_expected_effects.c.trace_id == trace_id)
        if not include_deleted:
            statement = statement.where(aion_expected_effects.c.deleted_at.is_(None))
        return [ExpectedEffect(**dict(row)) for row in self._all(statement)[:limit]]

    def soft_delete_expected_effect(self, expected_effect_id: str, reason: str) -> bool:
        effect = self.get_expected_effect(expected_effect_id)
        if effect is None:
            return False
        deleted = effect.model_copy(
            update={
                "deleted_at": datetime.now(UTC),
                "metadata": {**effect.metadata, "delete_reason": reason},
            }
        )
        self.save_expected_effect(deleted)
        return True

    def save_observed_effect(self, effect: ObservedEffect) -> ObservedEffect:
        self._upsert(
            aion_observed_effects,
            "observed_effect_id",
            effect.model_dump(mode="python"),
        )
        return effect

    def get_observed_effect(self, observed_effect_id: str) -> ObservedEffect | None:
        row = self._first(
            select(aion_observed_effects).where(
                aion_observed_effects.c.observed_effect_id == observed_effect_id
            )
        )
        return ObservedEffect(**dict(row)) if row is not None else None

    def list_observed_effects(
        self,
        *,
        outcome_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        trace_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ObservedEffect]:
        statement = select(aion_observed_effects).order_by(
            aion_observed_effects.c.created_at.desc()
        )
        if outcome_id:
            statement = statement.where(aion_observed_effects.c.outcome_id == outcome_id)
        if source_type:
            statement = statement.where(aion_observed_effects.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_observed_effects.c.source_id == source_id)
        if trace_id:
            statement = statement.where(aion_observed_effects.c.trace_id == trace_id)
        if not include_deleted:
            statement = statement.where(aion_observed_effects.c.deleted_at.is_(None))
        return [ObservedEffect(**dict(row)) for row in self._all(statement)[:limit]]

    def save_outcome(self, outcome: OutcomeRecord) -> OutcomeRecord:
        self._upsert(aion_outcome_records, "outcome_id", outcome.model_dump(mode="python"))
        return outcome

    def get_outcome(self, outcome_id: str) -> OutcomeRecord | None:
        row = self._first(
            select(aion_outcome_records).where(aion_outcome_records.c.outcome_id == outcome_id)
        )
        return OutcomeRecord(**dict(row)) if row is not None else None

    def get_outcome_by_source(self, source_type: str, source_id: str) -> OutcomeRecord | None:
        row = self._first(
            select(aion_outcome_records)
            .where(aion_outcome_records.c.source_type == source_type)
            .where(aion_outcome_records.c.source_id == source_id)
            .where(aion_outcome_records.c.deleted_at.is_(None))
            .order_by(aion_outcome_records.c.created_at.desc())
        )
        return OutcomeRecord(**dict(row)) if row is not None else None

    def list_outcomes(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[OutcomeRecord]:
        statement = select(aion_outcome_records).order_by(aion_outcome_records.c.created_at.desc())
        if status:
            statement = statement.where(aion_outcome_records.c.status == status)
        outcomes: list[OutcomeRecord] = []
        for row in self._all(statement):
            outcome = OutcomeRecord(**dict(row))
            if outcome.deleted_at is not None or not _scope_matches(outcome.owner_scope, scope):
                continue
            outcomes.append(outcome)
            if len(outcomes) >= limit:
                break
        return outcomes

    def query_outcomes(self, query: OutcomeQuery) -> list[OutcomeRecord]:
        statement = select(aion_outcome_records).order_by(aion_outcome_records.c.created_at.desc())
        if query.trace_id:
            statement = statement.where(aion_outcome_records.c.trace_id == query.trace_id)
        if query.source_types:
            statement = statement.where(aion_outcome_records.c.source_type.in_(query.source_types))
        if query.statuses:
            statement = statement.where(aion_outcome_records.c.status.in_(query.statuses))
        if query.outcome_types:
            statement = statement.where(
                aion_outcome_records.c.outcome_type.in_(query.outcome_types)
            )
        if query.min_score is not None:
            statement = statement.where(aion_outcome_records.c.score >= query.min_score)
        if not query.include_deleted:
            statement = statement.where(aion_outcome_records.c.deleted_at.is_(None))
        outcomes: list[OutcomeRecord] = []
        for row in self._all(statement):
            outcome = OutcomeRecord(**dict(row))
            if not _scope_matches(outcome.owner_scope, query.scope):
                continue
            if query.query and query.query.lower() not in _outcome_text(outcome):
                continue
            outcomes.append(outcome)
            if len(outcomes) >= query.limit:
                break
        return outcomes

    def save_verification_run(self, run: EffectVerificationRun) -> EffectVerificationRun:
        self._upsert(
            aion_effect_verification_runs,
            "verification_run_id",
            run.model_dump(mode="python"),
        )
        return run

    def get_verification_run(self, verification_run_id: str) -> EffectVerificationRun | None:
        row = self._first(
            select(aion_effect_verification_runs).where(
                aion_effect_verification_runs.c.verification_run_id == verification_run_id
            )
        )
        return EffectVerificationRun(**dict(row)) if row is not None else None

    def list_verification_runs(
        self,
        *,
        outcome_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[EffectVerificationRun]:
        statement = select(aion_effect_verification_runs).order_by(
            aion_effect_verification_runs.c.created_at.desc()
        )
        if outcome_id:
            statement = statement.where(aion_effect_verification_runs.c.outcome_id == outcome_id)
        if source_type:
            statement = statement.where(aion_effect_verification_runs.c.source_type == source_type)
        if source_id:
            statement = statement.where(aion_effect_verification_runs.c.source_id == source_id)
        if status:
            statement = statement.where(aion_effect_verification_runs.c.status == status)
        return [EffectVerificationRun(**dict(row)) for row in self._all(statement)[:limit]]

    def save_attribution(self, attribution: CausalAttribution) -> CausalAttribution:
        self._upsert(
            aion_causal_attributions,
            "causal_attribution_id",
            attribution.model_dump(mode="python"),
        )
        return attribution

    def get_attribution(self, causal_attribution_id: str) -> CausalAttribution | None:
        row = self._first(
            select(aion_causal_attributions).where(
                aion_causal_attributions.c.causal_attribution_id == causal_attribution_id
            )
        )
        return CausalAttribution(**dict(row)) if row is not None else None

    def list_attributions(
        self,
        *,
        outcome_id: str | None = None,
        cause_type: str | None = None,
        cause_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[CausalAttribution]:
        statement = select(aion_causal_attributions).order_by(
            aion_causal_attributions.c.created_at.desc()
        )
        if outcome_id:
            statement = statement.where(aion_causal_attributions.c.outcome_id == outcome_id)
        if cause_type:
            statement = statement.where(aion_causal_attributions.c.cause_type == cause_type)
        if cause_id:
            statement = statement.where(aion_causal_attributions.c.cause_id == cause_id)
        if not include_deleted:
            statement = statement.where(aion_causal_attributions.c.deleted_at.is_(None))
        return [CausalAttribution(**dict(row)) for row in self._all(statement)[:limit]]

    def soft_delete_attribution(self, causal_attribution_id: str, reason: str) -> bool:
        attribution = self.get_attribution(causal_attribution_id)
        if attribution is None:
            return False
        deleted = attribution.model_copy(
            update={
                "deleted_at": datetime.now(UTC),
                "metadata": {**attribution.metadata, "delete_reason": reason},
            }
        )
        self.save_attribution(deleted)
        return True

    def save_feedback(self, feedback: OutcomeFeedback) -> OutcomeFeedback:
        self._upsert(
            aion_outcome_feedback_records,
            "outcome_feedback_id",
            feedback.model_dump(mode="python"),
        )
        return feedback

    def get_feedback(self, outcome_feedback_id: str) -> OutcomeFeedback | None:
        row = self._first(
            select(aion_outcome_feedback_records).where(
                aion_outcome_feedback_records.c.outcome_feedback_id == outcome_feedback_id
            )
        )
        return OutcomeFeedback(**dict(row)) if row is not None else None

    def list_feedback(
        self,
        *,
        outcome_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[OutcomeFeedback]:
        statement = select(aion_outcome_feedback_records).order_by(
            aion_outcome_feedback_records.c.created_at.desc()
        )
        if outcome_id:
            statement = statement.where(aion_outcome_feedback_records.c.outcome_id == outcome_id)
        if status:
            statement = statement.where(aion_outcome_feedback_records.c.status == status)
        if severity:
            statement = statement.where(aion_outcome_feedback_records.c.severity == severity)
        return [OutcomeFeedback(**dict(row)) for row in self._all(statement)[:limit]]

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
            outcome_metadata.create_all(self._engine)
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


def _outcome_text(outcome: OutcomeRecord) -> str:
    return f"{outcome.title} {outcome.summary} {outcome.source_type} {outcome.source_id}".lower()


def now_utc() -> datetime:
    """Return current UTC time for outcome services."""
    return datetime.now(UTC)


__all__ = [
    "OutcomeRepository",
    "aion_causal_attributions",
    "aion_effect_verification_runs",
    "aion_expected_effects",
    "aion_observed_effects",
    "aion_outcome_feedback_records",
    "aion_outcome_records",
    "now_utc",
    "outcome_metadata",
]
