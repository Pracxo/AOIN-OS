"""Persistence for explanation records and trace narratives."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
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

from aion_brain.contracts.explanations import (
    ExplanationFeedback,
    ExplanationRecord,
    ExplanationStep,
    WhyNotAnswer,
)
from aion_brain.contracts.trace_narratives import TraceNarrative

explanation_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_explanation_records = Table(
    "aion_explanation_records",
    explanation_metadata,
    Column("explanation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("explanation_type", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("grounded", Boolean, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("decision_refs", json_payload_type, nullable=False),
    Column("outcome_refs", json_payload_type, nullable=False),
    Column("audit_refs", json_payload_type, nullable=False),
    Column("provenance_refs", json_payload_type, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("redaction_metadata", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_explanation_records_trace_id", "trace_id"),
    Index("ix_aion_explanation_records_actor_id", "actor_id"),
    Index("ix_aion_explanation_records_workspace_id", "workspace_id"),
    Index("ix_aion_explanation_records_explanation_type", "explanation_type"),
    Index("ix_aion_explanation_records_target_type", "target_type"),
    Index("ix_aion_explanation_records_target_id", "target_id"),
    Index("ix_aion_explanation_records_status", "status"),
    Index("ix_aion_explanation_records_confidence", "confidence"),
    Index("ix_aion_explanation_records_grounded", "grounded"),
    Index("ix_aion_explanation_records_created_at", "created_at"),
)

aion_explanation_steps = Table(
    "aion_explanation_steps",
    explanation_metadata,
    Column("explanation_step_id", Text, primary_key=True),
    Column(
        "explanation_id",
        Text,
        ForeignKey("aion_explanation_records.explanation_id"),
        nullable=False,
    ),
    Column("step_order", Integer, nullable=False),
    Column("step_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("refs", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_explanation_steps_explanation_id", "explanation_id"),
    Index("ix_aion_explanation_steps_step_order", "step_order"),
    Index("ix_aion_explanation_steps_step_type", "step_type"),
    Index("ix_aion_explanation_steps_source_type", "source_type"),
    Index("ix_aion_explanation_steps_source_id", "source_id"),
    Index("ix_aion_explanation_steps_confidence", "confidence"),
    Index("ix_aion_explanation_steps_created_at", "created_at"),
)

aion_trace_narratives = Table(
    "aion_trace_narratives",
    explanation_metadata,
    Column("trace_narrative_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("timeline", json_payload_type, nullable=False),
    Column("key_decisions", json_payload_type, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("approvals", json_payload_type, nullable=False),
    Column("outcomes", json_payload_type, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("audit_refs", json_payload_type, nullable=False),
    Column("redaction_metadata", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_trace_narratives_trace_id", "trace_id"),
    Index("ix_aion_trace_narratives_status", "status"),
    Index("ix_aion_trace_narratives_confidence", "confidence"),
    Index("ix_aion_trace_narratives_created_at", "created_at"),
)

aion_why_not_records = Table(
    "aion_why_not_records",
    explanation_metadata,
    Column("why_not_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("question", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("requested_action", Text, nullable=True),
    Column("answer", Text, nullable=False),
    Column("blockers", json_payload_type, nullable=False),
    Column("missing_requirements", json_payload_type, nullable=False),
    Column("next_possible_steps", json_payload_type, nullable=False),
    Column("refs", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_why_not_records_trace_id", "trace_id"),
    Index("ix_aion_why_not_records_actor_id", "actor_id"),
    Index("ix_aion_why_not_records_workspace_id", "workspace_id"),
    Index("ix_aion_why_not_records_target_type", "target_type"),
    Index("ix_aion_why_not_records_target_id", "target_id"),
    Index("ix_aion_why_not_records_requested_action", "requested_action"),
    Index("ix_aion_why_not_records_confidence", "confidence"),
    Index("ix_aion_why_not_records_created_at", "created_at"),
)

aion_explanation_feedback = Table(
    "aion_explanation_feedback",
    explanation_metadata,
    Column("explanation_feedback_id", Text, primary_key=True),
    Column("explanation_id", Text, nullable=True),
    Column("trace_narrative_id", Text, nullable=True),
    Column("why_not_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("feedback_type", Text, nullable=False),
    Column("rating", Integer, nullable=True),
    Column("comment", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_explanation_feedback_explanation_id", "explanation_id"),
    Index("ix_aion_explanation_feedback_trace_narrative_id", "trace_narrative_id"),
    Index("ix_aion_explanation_feedback_why_not_id", "why_not_id"),
    Index("ix_aion_explanation_feedback_actor_id", "actor_id"),
    Index("ix_aion_explanation_feedback_feedback_type", "feedback_type"),
    Index("ix_aion_explanation_feedback_rating", "rating"),
    Index("ix_aion_explanation_feedback_created_at", "created_at"),
)


class ExplanationRepository:
    """Repository for explanations, why-not answers, narratives, and feedback."""

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

    def save_explanation(self, explanation: ExplanationRecord) -> ExplanationRecord:
        """Persist an explanation and its ordered steps."""

        self._ensure_schema()
        stored = explanation.model_copy(
            update={"created_at": explanation.created_at or datetime.now(UTC)}
        )
        values = stored.model_dump(mode="python", exclude={"steps"})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_explanation_steps).where(
                    aion_explanation_steps.c.explanation_id == stored.explanation_id
                )
            )
            connection.execute(
                delete(aion_explanation_records).where(
                    aion_explanation_records.c.explanation_id == stored.explanation_id
                )
            )
            connection.execute(insert(aion_explanation_records).values(**values))
            for step in stored.steps:
                step_values = step.model_copy(
                    update={"created_at": step.created_at or stored.created_at}
                ).model_dump(mode="python")
                connection.execute(insert(aion_explanation_steps).values(**step_values))
        return stored

    def get_explanation(self, explanation_id: str) -> ExplanationRecord | None:
        """Return one persisted explanation."""

        self._ensure_schema()
        row = self._first(
            select(aion_explanation_records).where(
                aion_explanation_records.c.explanation_id == explanation_id
            )
        )
        return self._row_to_explanation(row) if row else None

    def list_explanations(
        self,
        *,
        trace_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        limit: int = 50,
    ) -> list[ExplanationRecord]:
        """List persisted explanations."""

        self._ensure_schema()
        statement = select(aion_explanation_records)
        if trace_id:
            statement = statement.where(aion_explanation_records.c.trace_id == trace_id)
        if target_type:
            statement = statement.where(aion_explanation_records.c.target_type == target_type)
        if target_id:
            statement = statement.where(aion_explanation_records.c.target_id == target_id)
        rows = self._all(
            statement.order_by(aion_explanation_records.c.created_at.desc()).limit(limit)
        )
        return [self._row_to_explanation(row) for row in rows]

    def save_trace_narrative(self, narrative: TraceNarrative) -> TraceNarrative:
        """Persist a trace narrative."""

        self._ensure_schema()
        stored = narrative.model_copy(
            update={"created_at": narrative.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_trace_narratives).where(
                    aion_trace_narratives.c.trace_narrative_id == stored.trace_narrative_id
                )
            )
            connection.execute(
                insert(aion_trace_narratives).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_trace_narrative(self, trace_narrative_id: str) -> TraceNarrative | None:
        """Return one trace narrative."""

        self._ensure_schema()
        row = self._first(
            select(aion_trace_narratives).where(
                aion_trace_narratives.c.trace_narrative_id == trace_narrative_id
            )
        )
        return _row_to_trace_narrative(row) if row else None

    def list_trace_narratives(
        self,
        *,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> list[TraceNarrative]:
        """List persisted trace narratives."""

        self._ensure_schema()
        statement = select(aion_trace_narratives)
        if trace_id:
            statement = statement.where(aion_trace_narratives.c.trace_id == trace_id)
        rows = self._all(statement.order_by(aion_trace_narratives.c.created_at.desc()).limit(limit))
        return [_row_to_trace_narrative(row) for row in rows]

    def save_why_not(self, answer: WhyNotAnswer) -> WhyNotAnswer:
        """Persist a why-not answer."""

        self._ensure_schema()
        stored = answer.model_copy(update={"created_at": answer.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_why_not_records).where(
                    aion_why_not_records.c.why_not_id == stored.why_not_id
                )
            )
            connection.execute(
                insert(aion_why_not_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_why_not(self, why_not_id: str) -> WhyNotAnswer | None:
        """Return one why-not answer."""

        self._ensure_schema()
        row = self._first(
            select(aion_why_not_records).where(aion_why_not_records.c.why_not_id == why_not_id)
        )
        return _row_to_why_not(row) if row else None

    def list_why_not(
        self,
        *,
        trace_id: str | None = None,
        target_type: str | None = None,
        limit: int = 50,
    ) -> list[WhyNotAnswer]:
        """List why-not answers."""

        self._ensure_schema()
        statement = select(aion_why_not_records)
        if trace_id:
            statement = statement.where(aion_why_not_records.c.trace_id == trace_id)
        if target_type:
            statement = statement.where(aion_why_not_records.c.target_type == target_type)
        rows = self._all(statement.order_by(aion_why_not_records.c.created_at.desc()).limit(limit))
        return [_row_to_why_not(row) for row in rows]

    def save_feedback(self, feedback: ExplanationFeedback) -> ExplanationFeedback:
        """Persist explanation feedback."""

        self._ensure_schema()
        stored = feedback.model_copy(
            update={"created_at": feedback.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_explanation_feedback).where(
                    aion_explanation_feedback.c.explanation_feedback_id
                    == stored.explanation_feedback_id
                )
            )
            connection.execute(
                insert(aion_explanation_feedback).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_feedback(
        self,
        *,
        explanation_id: str | None = None,
        trace_narrative_id: str | None = None,
        why_not_id: str | None = None,
        limit: int = 100,
    ) -> list[ExplanationFeedback]:
        """List explanation feedback."""

        self._ensure_schema()
        statement = select(aion_explanation_feedback)
        if explanation_id:
            statement = statement.where(
                aion_explanation_feedback.c.explanation_id == explanation_id
            )
        if trace_narrative_id:
            statement = statement.where(
                aion_explanation_feedback.c.trace_narrative_id == trace_narrative_id
            )
        if why_not_id:
            statement = statement.where(aion_explanation_feedback.c.why_not_id == why_not_id)
        rows = self._all(
            statement.order_by(aion_explanation_feedback.c.created_at.desc()).limit(limit)
        )
        return [_row_to_feedback(row) for row in rows]

    def _row_to_explanation(self, row: RowMapping) -> ExplanationRecord:
        steps = [
            _row_to_step(step)
            for step in self._all(
                select(aion_explanation_steps)
                .where(aion_explanation_steps.c.explanation_id == row["explanation_id"])
                .order_by(aion_explanation_steps.c.step_order)
            )
        ]
        return ExplanationRecord(
            explanation_id=str(row["explanation_id"]),
            trace_id=_optional_str(row["trace_id"]),
            actor_id=_optional_str(row["actor_id"]),
            workspace_id=_optional_str(row["workspace_id"]),
            explanation_type=cast(Any, str(row["explanation_type"])),
            target_type=cast(Any, str(row["target_type"])),
            target_id=_optional_str(row["target_id"]),
            status=cast(Any, str(row["status"])),
            title=str(row["title"]),
            summary=str(row["summary"]),
            confidence=float(row["confidence"]),
            grounded=bool(row["grounded"]),
            evidence_refs=_string_list(row["evidence_refs"]),
            memory_refs=_string_list(row["memory_refs"]),
            belief_refs=_string_list(row["belief_refs"]),
            decision_refs=_string_list(row["decision_refs"]),
            outcome_refs=_string_list(row["outcome_refs"]),
            audit_refs=_string_list(row["audit_refs"]),
            provenance_refs=_string_list(row["provenance_refs"]),
            policy_decision_id=_optional_str(row["policy_decision_id"]),
            autonomy_decision_id=_optional_str(row["autonomy_decision_id"]),
            risk_assessment_id=_optional_str(row["risk_assessment_id"]),
            approval_request_id=_optional_str(row["approval_request_id"]),
            steps=steps,
            redaction_metadata=dict(row["redaction_metadata"]),
            constraints=_string_list(row["constraints"]),
            metadata=dict(row["metadata"]),
            created_by=_optional_str(row["created_by"]),
            created_at=_datetime(row["created_at"]),
        )

    def _first(self, statement: Any) -> RowMapping | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _all(self, statement: Any) -> list[RowMapping]:
        self._ensure_schema()
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        explanation_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_step(row: RowMapping) -> ExplanationStep:
    return ExplanationStep(
        explanation_step_id=str(row["explanation_step_id"]),
        explanation_id=str(row["explanation_id"]),
        step_order=int(row["step_order"]),
        step_type=cast(Any, str(row["step_type"])),
        title=str(row["title"]),
        description=str(row["description"]),
        source_type=_optional_str(row["source_type"]),
        source_id=_optional_str(row["source_id"]),
        refs=_string_list(row["refs"]),
        confidence=float(row["confidence"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_trace_narrative(row: RowMapping) -> TraceNarrative:
    return TraceNarrative(
        trace_narrative_id=str(row["trace_narrative_id"]),
        trace_id=str(row["trace_id"]),
        status=cast(Any, str(row["status"])),
        title=str(row["title"]),
        summary=str(row["summary"]),
        timeline=list(row["timeline"]),
        key_decisions=list(row["key_decisions"]),
        blockers=list(row["blockers"]),
        approvals=list(row["approvals"]),
        outcomes=list(row["outcomes"]),
        evidence_refs=_string_list(row["evidence_refs"]),
        audit_refs=_string_list(row["audit_refs"]),
        confidence=float(row["confidence"]),
        redaction_metadata=dict(row["redaction_metadata"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_why_not(row: RowMapping) -> WhyNotAnswer:
    return WhyNotAnswer(
        why_not_id=str(row["why_not_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        question=str(row["question"]),
        target_type=cast(Any, str(row["target_type"])),
        target_id=_optional_str(row["target_id"]),
        requested_action=_optional_str(row["requested_action"]),
        answer=str(row["answer"]),
        blockers=list(row["blockers"]),
        missing_requirements=_string_list(row["missing_requirements"]),
        next_possible_steps=_string_list(row["next_possible_steps"]),
        refs=_string_list(row["refs"]),
        confidence=float(row["confidence"]),
        metadata=dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_feedback(row: RowMapping) -> ExplanationFeedback:
    return ExplanationFeedback(
        explanation_feedback_id=str(row["explanation_feedback_id"]),
        explanation_id=_optional_str(row["explanation_id"]),
        trace_narrative_id=_optional_str(row["trace_narrative_id"]),
        why_not_id=_optional_str(row["why_not_id"]),
        actor_id=_optional_str(row["actor_id"]),
        feedback_type=cast(Any, str(row["feedback_type"])),
        rating=int(row["rating"]) if row["rating"] is not None else None,
        comment=_optional_str(row["comment"]),
        metadata=dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


__all__ = [
    "ExplanationRepository",
    "aion_explanation_feedback",
    "aion_explanation_records",
    "aion_explanation_steps",
    "aion_trace_narratives",
    "aion_why_not_records",
    "explanation_metadata",
]
