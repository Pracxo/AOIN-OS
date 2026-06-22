"""Persistence for experience and learning synthesis records."""

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
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.experience import ExperienceQuery, ExperienceRecord
from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LearningSynthesisRun,
    LessonRecord,
    PatternMiningRun,
    RegressionCandidateSuggestion,
    SkillCandidateSuggestion,
)

learning_synthesis_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_experience_records = Table(
    "aion_experience_records",
    learning_synthesis_metadata,
    Column("experience_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("experience_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("outcome_refs", json_payload_type, nullable=False),
    Column("decision_refs", json_payload_type, nullable=False),
    Column("command_refs", json_payload_type, nullable=False),
    Column("workflow_refs", json_payload_type, nullable=False),
    Column("regression_refs", json_payload_type, nullable=False),
    Column("replay_refs", json_payload_type, nullable=False),
    Column("audit_refs", json_payload_type, nullable=False),
    Column("signal_refs", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_experience_records_trace_id", "trace_id"),
    Index("ix_aion_experience_records_actor_id", "actor_id"),
    Index("ix_aion_experience_records_workspace_id", "workspace_id"),
    Index("ix_aion_experience_records_source_type", "source_type"),
    Index("ix_aion_experience_records_source_id", "source_id"),
    Index("ix_aion_experience_records_experience_type", "experience_type"),
    Index("ix_aion_experience_records_status", "status"),
    Index("ix_aion_experience_records_score", "score"),
    Index("ix_aion_experience_records_confidence", "confidence"),
    Index("ix_aion_experience_records_observed_at", "observed_at"),
    Index("ix_aion_experience_records_created_at", "created_at"),
    Index("ix_aion_experience_records_deleted_at", "deleted_at"),
)

aion_learning_patterns = Table(
    "aion_learning_patterns",
    learning_synthesis_metadata,
    Column("pattern_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("pattern_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("experience_refs", json_payload_type, nullable=False),
    Column("outcome_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("frequency", Integer, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("severity", Text, nullable=False),
    Column("recommendation", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_learning_patterns_trace_id", "trace_id"),
    Index("ix_aion_learning_patterns_pattern_type", "pattern_type"),
    Index("ix_aion_learning_patterns_status", "status"),
    Index("ix_aion_learning_patterns_frequency", "frequency"),
    Index("ix_aion_learning_patterns_confidence", "confidence"),
    Index("ix_aion_learning_patterns_severity", "severity"),
    Index("ix_aion_learning_patterns_created_at", "created_at"),
)

aion_lesson_records = Table(
    "aion_lesson_records",
    learning_synthesis_metadata,
    Column("lesson_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("lesson_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("lesson", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("pattern_refs", json_payload_type, nullable=False),
    Column("experience_refs", json_payload_type, nullable=False),
    Column("outcome_refs", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("applicability", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=True),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_lesson_records_trace_id", "trace_id"),
    Index("ix_aion_lesson_records_lesson_type", "lesson_type"),
    Index("ix_aion_lesson_records_status", "status"),
    Index("ix_aion_lesson_records_confidence", "confidence"),
    Index("ix_aion_lesson_records_created_at", "created_at"),
)

aion_learning_synthesis_runs = Table(
    "aion_learning_synthesis_runs",
    learning_synthesis_metadata,
    Column("synthesis_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input_refs", json_payload_type, nullable=False),
    Column("experience_ids", json_payload_type, nullable=False),
    Column("pattern_ids", json_payload_type, nullable=False),
    Column("lesson_ids", json_payload_type, nullable=False),
    Column("reflection_candidate_ids", json_payload_type, nullable=False),
    Column("skill_candidate_suggestion_ids", json_payload_type, nullable=False),
    Column("regression_candidate_suggestion_ids", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_learning_synthesis_runs_trace_id", "trace_id"),
    Index("ix_aion_learning_synthesis_runs_actor_id", "actor_id"),
    Index("ix_aion_learning_synthesis_runs_workspace_id", "workspace_id"),
    Index("ix_aion_learning_synthesis_runs_status", "status"),
    Index("ix_aion_learning_synthesis_runs_mode", "mode"),
    Index("ix_aion_learning_synthesis_runs_created_at", "created_at"),
)

aion_pattern_mining_runs = Table(
    "aion_pattern_mining_runs",
    learning_synthesis_metadata,
    Column("pattern_mining_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("mining_type", Text, nullable=False),
    Column("input_experience_ids", json_payload_type, nullable=False),
    Column("pattern_ids", json_payload_type, nullable=False),
    Column("skipped", Integer, nullable=False),
    Column("failed", Integer, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_pattern_mining_runs_trace_id", "trace_id"),
    Index("ix_aion_pattern_mining_runs_actor_id", "actor_id"),
    Index("ix_aion_pattern_mining_runs_workspace_id", "workspace_id"),
    Index("ix_aion_pattern_mining_runs_status", "status"),
    Index("ix_aion_pattern_mining_runs_mining_type", "mining_type"),
    Index("ix_aion_pattern_mining_runs_created_at", "created_at"),
)

aion_skill_candidate_suggestions = Table(
    "aion_skill_candidate_suggestions",
    learning_synthesis_metadata,
    Column("suggestion_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("pattern_id", Text, nullable=True),
    Column("lesson_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("proposed_skill_type", Text, nullable=False),
    Column("source_refs", json_payload_type, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("promotion_allowed", Boolean, nullable=False),
    Column("skill_candidate_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_skill_candidate_suggestions_trace_id", "trace_id"),
    Index("ix_aion_skill_candidate_suggestions_pattern_id", "pattern_id"),
    Index("ix_aion_skill_candidate_suggestions_lesson_id", "lesson_id"),
    Index("ix_aion_skill_candidate_suggestions_status", "status"),
    Index("ix_aion_skill_candidate_suggestions_proposed_skill_type", "proposed_skill_type"),
    Index("ix_aion_skill_candidate_suggestions_risk_level", "risk_level"),
    Index("ix_aion_skill_candidate_suggestions_confidence", "confidence"),
    Index("ix_aion_skill_candidate_suggestions_promotion_allowed", "promotion_allowed"),
    Index("ix_aion_skill_candidate_suggestions_created_at", "created_at"),
)

aion_regression_candidate_suggestions = Table(
    "aion_regression_candidate_suggestions",
    learning_synthesis_metadata,
    Column("regression_suggestion_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("pattern_id", Text, nullable=True),
    Column("outcome_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_refs", json_payload_type, nullable=False),
    Column("severity", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("regression_case_id", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=True),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_regression_candidate_suggestions_trace_id", "trace_id"),
    Index("ix_aion_regression_candidate_suggestions_pattern_id", "pattern_id"),
    Index("ix_aion_regression_candidate_suggestions_outcome_id", "outcome_id"),
    Index("ix_aion_regression_candidate_suggestions_status", "status"),
    Index("ix_aion_regression_candidate_suggestions_severity", "severity"),
    Index("ix_aion_regression_candidate_suggestions_confidence", "confidence"),
    Index("ix_aion_regression_candidate_suggestions_created_at", "created_at"),
)


class LearningSynthesisRepository:
    """Repository for experience and synthesized learning records."""

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

    def save_experience(self, experience: ExperienceRecord) -> ExperienceRecord:
        self._upsert(
            aion_experience_records,
            "experience_id",
            experience.model_dump(mode="python"),
        )
        return experience

    def get_experience(self, experience_id: str) -> ExperienceRecord | None:
        row = self._first(
            select(aion_experience_records).where(
                aion_experience_records.c.experience_id == experience_id
            )
        )
        return ExperienceRecord(**dict(row)) if row is not None else None

    def get_experience_by_source(
        self,
        source_type: str,
        source_id: str,
    ) -> ExperienceRecord | None:
        row = self._first(
            select(aion_experience_records)
            .where(aion_experience_records.c.source_type == source_type)
            .where(aion_experience_records.c.source_id == source_id)
            .where(aion_experience_records.c.deleted_at.is_(None))
            .order_by(aion_experience_records.c.created_at.desc())
        )
        return ExperienceRecord(**dict(row)) if row is not None else None

    def query_experiences(self, query: ExperienceQuery) -> list[ExperienceRecord]:
        statement = select(aion_experience_records).order_by(
            aion_experience_records.c.created_at.desc()
        )
        if query.trace_id:
            statement = statement.where(aion_experience_records.c.trace_id == query.trace_id)
        if query.source_types:
            statement = statement.where(
                aion_experience_records.c.source_type.in_(query.source_types)
            )
        if query.experience_types:
            statement = statement.where(
                aion_experience_records.c.experience_type.in_(query.experience_types)
            )
        if query.statuses:
            statement = statement.where(aion_experience_records.c.status.in_(query.statuses))
        if query.min_score is not None:
            statement = statement.where(aion_experience_records.c.score >= query.min_score)
        if query.min_confidence is not None:
            statement = statement.where(
                aion_experience_records.c.confidence >= query.min_confidence
            )
        if not query.include_archived:
            statement = statement.where(aion_experience_records.c.status == "active")
        statement = statement.where(aion_experience_records.c.deleted_at.is_(None))
        results: list[ExperienceRecord] = []
        for row in self._all(statement):
            record = ExperienceRecord(**dict(row))
            if not _scope_matches(record.owner_scope, query.scope):
                continue
            if query.query and query.query.lower() not in _experience_text(record):
                continue
            results.append(record)
            if len(results) >= query.limit:
                break
        return results

    def list_experiences(
        self,
        scope: list[str],
        *,
        experience_types: list[str] | None = None,
        limit: int = 500,
    ) -> list[ExperienceRecord]:
        query = ExperienceQuery(
            scope=scope,
            experience_types=experience_types or [],
            include_archived=False,
            limit=limit,
        )
        return self.query_experiences(query)

    def save_pattern(self, pattern: LearningPattern) -> LearningPattern:
        self._upsert(aion_learning_patterns, "pattern_id", pattern.model_dump(mode="python"))
        return pattern

    def get_pattern(self, pattern_id: str) -> LearningPattern | None:
        row = self._first(
            select(aion_learning_patterns).where(aion_learning_patterns.c.pattern_id == pattern_id)
        )
        return LearningPattern(**dict(row)) if row is not None else None

    def list_patterns(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        pattern_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[LearningPattern]:
        statement = select(aion_learning_patterns).order_by(
            aion_learning_patterns.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_learning_patterns.c.status == status)
        if pattern_type:
            statement = statement.where(aion_learning_patterns.c.pattern_type == pattern_type)
        if severity:
            statement = statement.where(aion_learning_patterns.c.severity == severity)
        return _filter_scope(
            [LearningPattern(**dict(row)) for row in self._all(statement)],
            scope,
            limit,
        )

    def save_lesson(self, lesson: LessonRecord) -> LessonRecord:
        self._upsert(aion_lesson_records, "lesson_id", lesson.model_dump(mode="python"))
        return lesson

    def get_lesson(self, lesson_id: str) -> LessonRecord | None:
        row = self._first(
            select(aion_lesson_records).where(aion_lesson_records.c.lesson_id == lesson_id)
        )
        return LessonRecord(**dict(row)) if row is not None else None

    def list_lessons(
        self,
        scope: list[str],
        *,
        lesson_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[LessonRecord]:
        statement = select(aion_lesson_records).order_by(aion_lesson_records.c.created_at.desc())
        if lesson_type:
            statement = statement.where(aion_lesson_records.c.lesson_type == lesson_type)
        if status:
            statement = statement.where(aion_lesson_records.c.status == status)
        return _filter_scope(
            [LessonRecord(**dict(row)) for row in self._all(statement)],
            scope,
            limit,
        )

    def save_mining_run(self, run: PatternMiningRun) -> PatternMiningRun:
        values = run.model_dump(mode="python", exclude={"patterns"})
        values["pattern_ids"] = [pattern.pattern_id for pattern in run.patterns]
        self._upsert(aion_pattern_mining_runs, "pattern_mining_run_id", values)
        return run

    def get_mining_run(self, pattern_mining_run_id: str) -> PatternMiningRun | None:
        row = self._first(
            select(aion_pattern_mining_runs).where(
                aion_pattern_mining_runs.c.pattern_mining_run_id == pattern_mining_run_id
            )
        )
        if row is None:
            return None
        data = dict(row)
        pattern_ids = _str_list(data.pop("pattern_ids"))
        data["patterns"] = [
            pattern
            for pattern_id in pattern_ids
            if (pattern := self.get_pattern(pattern_id)) is not None
        ]
        return PatternMiningRun(**data)

    def save_synthesis_run(self, run: LearningSynthesisRun) -> LearningSynthesisRun:
        values = run.model_dump(
            mode="python",
            exclude={
                "experiences",
                "patterns",
                "lessons",
                "skill_candidate_suggestions",
                "regression_candidate_suggestions",
            },
        )
        values["experience_ids"] = [item.experience_id for item in run.experiences]
        values["pattern_ids"] = [item.pattern_id for item in run.patterns]
        values["lesson_ids"] = [item.lesson_id for item in run.lessons]
        values["skill_candidate_suggestion_ids"] = [
            item.suggestion_id for item in run.skill_candidate_suggestions
        ]
        values["regression_candidate_suggestion_ids"] = [
            item.regression_suggestion_id for item in run.regression_candidate_suggestions
        ]
        self._upsert(aion_learning_synthesis_runs, "synthesis_run_id", values)
        return run

    def get_synthesis_run(self, synthesis_run_id: str) -> LearningSynthesisRun | None:
        row = self._first(
            select(aion_learning_synthesis_runs).where(
                aion_learning_synthesis_runs.c.synthesis_run_id == synthesis_run_id
            )
        )
        if row is None:
            return None
        data = dict(row)
        data["experiences"] = [
            experience
            for item_id in _str_list(data.pop("experience_ids"))
            if (experience := self.get_experience(item_id)) is not None
        ]
        data["patterns"] = [
            pattern
            for item_id in _str_list(data.pop("pattern_ids"))
            if (pattern := self.get_pattern(item_id)) is not None
        ]
        data["lessons"] = [
            lesson
            for item_id in _str_list(data.pop("lesson_ids"))
            if (lesson := self.get_lesson(item_id)) is not None
        ]
        data["skill_candidate_suggestions"] = [
            skill_suggestion
            for item_id in _str_list(data.pop("skill_candidate_suggestion_ids"))
            if (skill_suggestion := self.get_skill_suggestion(item_id)) is not None
        ]
        data["regression_candidate_suggestions"] = [
            regression_suggestion
            for item_id in _str_list(data.pop("regression_candidate_suggestion_ids"))
            if (regression_suggestion := self.get_regression_suggestion(item_id)) is not None
        ]
        return LearningSynthesisRun(**data)

    def list_synthesis_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[LearningSynthesisRun]:
        statement = select(aion_learning_synthesis_runs).order_by(
            aion_learning_synthesis_runs.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_learning_synthesis_runs.c.status == status)
        rows = self._all(statement.limit(limit))
        return [
            run
            for row in rows
            if (run := self.get_synthesis_run(str(row["synthesis_run_id"]))) is not None
            and _scope_matches(run.owner_scope, scope)
        ]

    def save_skill_suggestion(
        self,
        suggestion: SkillCandidateSuggestion,
    ) -> SkillCandidateSuggestion:
        self._upsert(
            aion_skill_candidate_suggestions,
            "suggestion_id",
            suggestion.model_dump(mode="python"),
        )
        return suggestion

    def get_skill_suggestion(self, suggestion_id: str) -> SkillCandidateSuggestion | None:
        row = self._first(
            select(aion_skill_candidate_suggestions).where(
                aion_skill_candidate_suggestions.c.suggestion_id == suggestion_id
            )
        )
        return SkillCandidateSuggestion(**dict(row)) if row is not None else None

    def list_skill_suggestions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SkillCandidateSuggestion]:
        statement = select(aion_skill_candidate_suggestions).order_by(
            aion_skill_candidate_suggestions.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_skill_candidate_suggestions.c.status == status)
        return _filter_scope(
            [SkillCandidateSuggestion(**dict(row)) for row in self._all(statement)],
            scope,
            limit,
        )

    def save_regression_suggestion(
        self,
        suggestion: RegressionCandidateSuggestion,
    ) -> RegressionCandidateSuggestion:
        self._upsert(
            aion_regression_candidate_suggestions,
            "regression_suggestion_id",
            suggestion.model_dump(mode="python"),
        )
        return suggestion

    def get_regression_suggestion(
        self,
        regression_suggestion_id: str,
    ) -> RegressionCandidateSuggestion | None:
        row = self._first(
            select(aion_regression_candidate_suggestions).where(
                aion_regression_candidate_suggestions.c.regression_suggestion_id
                == regression_suggestion_id
            )
        )
        return RegressionCandidateSuggestion(**dict(row)) if row is not None else None

    def list_regression_suggestions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[RegressionCandidateSuggestion]:
        statement = select(aion_regression_candidate_suggestions).order_by(
            aion_regression_candidate_suggestions.c.created_at.desc()
        )
        if status:
            statement = statement.where(aion_regression_candidate_suggestions.c.status == status)
        if severity:
            statement = statement.where(
                aion_regression_candidate_suggestions.c.severity == severity
            )
        return _filter_scope(
            [RegressionCandidateSuggestion(**dict(row)) for row in self._all(statement)],
            scope,
            limit,
        )

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
            learning_synthesis_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return connection.execute(statement).mappings().first()

    def _all(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.begin() as connection:
            return list(connection.execute(statement).mappings().all())


def _filter_scope(items: list[Any], scope: list[str], limit: int) -> list[Any]:
    filtered: list[Any] = []
    for item in items:
        if _scope_matches(item.owner_scope, scope):
            filtered.append(item)
        if len(filtered) >= limit:
            break
    return filtered


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))


def _experience_text(experience: ExperienceRecord) -> str:
    return (
        f"{experience.title} {experience.summary} {experience.source_type} {experience.source_id}"
    ).lower()


def _str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def now_utc() -> datetime:
    """Return current UTC time for learning synthesis services."""
    return datetime.now(UTC)


__all__ = [
    "LearningSynthesisRepository",
    "aion_experience_records",
    "aion_learning_patterns",
    "aion_learning_synthesis_runs",
    "aion_lesson_records",
    "aion_pattern_mining_runs",
    "aion_regression_candidate_suggestions",
    "aion_skill_candidate_suggestions",
    "learning_synthesis_metadata",
    "now_utc",
]
