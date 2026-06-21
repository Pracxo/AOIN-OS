"""Persistent repository for model output governance."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.model_outputs import (
    ModelOutputRecord,
    ModelOutputSegment,
    ResponseCandidate,
    StructuredOutputValidation,
    ToolIntentCandidate,
)
from aion_brain.contracts.output_governance import (
    ModelOutputQuery,
    ModelOutputQueryResult,
    OutputGovernanceRun,
)

model_output_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_model_output_records = Table(
    "aion_model_output_records",
    model_output_metadata,
    Column("model_output_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("prompt_packet_id", Text, nullable=True),
    Column("model_input_manifest_id", Text, nullable=True),
    Column("model_route", Text, nullable=True),
    Column("provider_type", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("output_type", Text, nullable=False),
    Column("raw_output_hash", Text, nullable=False),
    Column("redacted_output", Text, nullable=False),
    Column("output_redacted", Boolean, nullable=False),
    Column("token_estimate", Integer, nullable=False),
    Column("char_count", Integer, nullable=False),
    Column("safety_findings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_model_outputs_trace_id", "trace_id"),
    Index("ix_aion_model_outputs_actor_id", "actor_id"),
    Index("ix_aion_model_outputs_workspace_id", "workspace_id"),
    Index("ix_aion_model_outputs_prompt_packet_id", "prompt_packet_id"),
    Index("ix_aion_model_outputs_model_input_manifest_id", "model_input_manifest_id"),
    Index("ix_aion_model_outputs_model_route", "model_route"),
    Index("ix_aion_model_outputs_provider_type", "provider_type"),
    Index("ix_aion_model_outputs_status", "status"),
    Index("ix_aion_model_outputs_output_type", "output_type"),
    Index("ix_aion_model_outputs_raw_output_hash", "raw_output_hash"),
    Index("ix_aion_model_outputs_created_at", "created_at"),
    Index("ix_aion_model_outputs_deleted_at", "deleted_at"),
)

aion_model_output_segments = Table(
    "aion_model_output_segments",
    model_output_metadata,
    Column("output_segment_id", Text, primary_key=True),
    Column(
        "model_output_id",
        Text,
        ForeignKey("aion_model_output_records.model_output_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("segment_order", Integer, nullable=False),
    Column("segment_type", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("unsafe", Boolean, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_output_segments_model_output_id", "model_output_id"),
    Index("ix_aion_output_segments_trace_id", "trace_id"),
    Index("ix_aion_output_segments_segment_order", "segment_order"),
    Index("ix_aion_output_segments_segment_type", "segment_type"),
    Index("ix_aion_output_segments_content_hash", "content_hash"),
    Index("ix_aion_output_segments_confidence", "confidence"),
    Index("ix_aion_output_segments_unsafe", "unsafe"),
    Index("ix_aion_output_segments_created_at", "created_at"),
    Index("ix_aion_output_segments_deleted_at", "deleted_at"),
)

aion_structured_output_validations = Table(
    "aion_structured_output_validations",
    model_output_metadata,
    Column("structured_validation_id", Text, primary_key=True),
    Column(
        "model_output_id",
        Text,
        ForeignKey("aion_model_output_records.model_output_id"),
        nullable=False,
    ),
    Column("trace_id", Text, nullable=True),
    Column("schema_name", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("valid", Boolean, nullable=False),
    Column("parsed_payload", json_payload_type, nullable=False),
    Column("schema_errors", json_payload_type, nullable=False),
    Column("safety_errors", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_structured_validations_model_output_id", "model_output_id"),
    Index("ix_aion_structured_validations_trace_id", "trace_id"),
    Index("ix_aion_structured_validations_schema_name", "schema_name"),
    Index("ix_aion_structured_validations_status", "status"),
    Index("ix_aion_structured_validations_valid", "valid"),
    Index("ix_aion_structured_validations_created_at", "created_at"),
)

aion_response_candidates = Table(
    "aion_response_candidates",
    model_output_metadata,
    Column("response_candidate_id", Text, primary_key=True),
    Column("model_output_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("dialogue_session_id", Text, nullable=True),
    Column("prompt_packet_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("response_type", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("grounded", Boolean, nullable=False),
    Column("citation_refs", json_payload_type, nullable=False),
    Column("grounding_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("entity_refs", json_payload_type, nullable=False),
    Column("unsupported_statement_refs", json_payload_type, nullable=False),
    Column("verification_refs", json_payload_type, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("score", Float, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("promoted_response_id", Text, nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_response_candidates_model_output_id", "model_output_id"),
    Index("ix_aion_response_candidates_trace_id", "trace_id"),
    Index("ix_aion_response_candidates_dialogue_session_id", "dialogue_session_id"),
    Index("ix_aion_response_candidates_prompt_packet_id", "prompt_packet_id"),
    Index("ix_aion_response_candidates_status", "status"),
    Index("ix_aion_response_candidates_response_type", "response_type"),
    Index("ix_aion_response_candidates_grounded", "grounded"),
    Index("ix_aion_response_candidates_confidence", "confidence"),
    Index("ix_aion_response_candidates_score", "score"),
    Index("ix_aion_response_candidates_created_at", "created_at"),
    Index("ix_aion_response_candidates_deleted_at", "deleted_at"),
)

aion_tool_intent_candidates = Table(
    "aion_tool_intent_candidates",
    model_output_metadata,
    Column("tool_intent_id", Text, primary_key=True),
    Column("model_output_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("prompt_packet_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("intent_type", Text, nullable=False),
    Column("tool_name", Text, nullable=True),
    Column("action_type", Text, nullable=True),
    Column("target_type", Text, nullable=True),
    Column("target_id", Text, nullable=True),
    Column("arguments_redacted", json_payload_type, nullable=False),
    Column("raw_arguments_hash", Text, nullable=True),
    Column("risk_level", Text, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("autonomy_decision_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("blocked_reason", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_tool_intents_model_output_id", "model_output_id"),
    Index("ix_aion_tool_intents_trace_id", "trace_id"),
    Index("ix_aion_tool_intents_prompt_packet_id", "prompt_packet_id"),
    Index("ix_aion_tool_intents_status", "status"),
    Index("ix_aion_tool_intents_intent_type", "intent_type"),
    Index("ix_aion_tool_intents_tool_name", "tool_name"),
    Index("ix_aion_tool_intents_action_type", "action_type"),
    Index("ix_aion_tool_intents_target_type", "target_type"),
    Index("ix_aion_tool_intents_risk_level", "risk_level"),
    Index("ix_aion_tool_intents_created_at", "created_at"),
)

aion_output_governance_runs = Table(
    "aion_output_governance_runs",
    model_output_metadata,
    Column("output_governance_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column(
        "model_output_id",
        Text,
        ForeignKey("aion_model_output_records.model_output_id"),
        nullable=False,
    ),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("parsed_segment_ids", json_payload_type, nullable=False),
    Column("response_candidate_ids", json_payload_type, nullable=False),
    Column("tool_intent_ids", json_payload_type, nullable=False),
    Column("structured_validation_ids", json_payload_type, nullable=False),
    Column("blocked", Boolean, nullable=False),
    Column("issues", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_output_governance_trace_id", "trace_id"),
    Index("ix_aion_output_governance_model_output_id", "model_output_id"),
    Index("ix_aion_output_governance_status", "status"),
    Index("ix_aion_output_governance_blocked", "blocked"),
    Index("ix_aion_output_governance_score", "score"),
    Index("ix_aion_output_governance_created_at", "created_at"),
)


class ModelOutputRepository:
    """Repository for model output governance contracts."""

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

    def save_output(self, output: ModelOutputRecord) -> ModelOutputRecord:
        self._ensure_schema()
        stored = output.model_copy(update={"created_at": output.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_model_output_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_output(self, model_output_id: str) -> ModelOutputRecord | None:
        self._ensure_schema()
        statement = select(aion_model_output_records).where(
            aion_model_output_records.c.model_output_id == model_output_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return ModelOutputRecord(**dict(row)) if row is not None else None

    def list_outputs(self, query: ModelOutputQuery) -> list[ModelOutputRecord]:
        self._ensure_schema()
        statement = select(aion_model_output_records).order_by(
            aion_model_output_records.c.created_at.desc()
        )
        if query.trace_id is not None:
            statement = statement.where(aion_model_output_records.c.trace_id == query.trace_id)
        if query.prompt_packet_id is not None:
            statement = statement.where(
                aion_model_output_records.c.prompt_packet_id == query.prompt_packet_id
            )
        if query.model_route is not None:
            statement = statement.where(
                aion_model_output_records.c.model_route == query.model_route
            )
        if query.status is not None:
            statement = statement.where(aion_model_output_records.c.status == query.status)
        if query.output_type is not None:
            statement = statement.where(
                aion_model_output_records.c.output_type == query.output_type
            )
        if not query.include_deleted:
            statement = statement.where(aion_model_output_records.c.deleted_at.is_(None))
        statement = statement.limit(query.limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ModelOutputRecord(**dict(row)) for row in rows]

    def soft_delete_output(self, model_output_id: str) -> bool:
        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_model_output_records)
                .where(aion_model_output_records.c.model_output_id == model_output_id)
                .values(deleted_at=datetime.now(UTC), status="archived")
            )
        return bool(result.rowcount)

    def update_output_status(self, model_output_id: str, status: str) -> bool:
        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_model_output_records)
                .where(aion_model_output_records.c.model_output_id == model_output_id)
                .values(status=status)
            )
        return bool(result.rowcount)

    def save_segments(self, segments: list[ModelOutputSegment]) -> list[ModelOutputSegment]:
        self._ensure_schema()
        if not segments:
            return []
        stored = [
            segment.model_copy(update={"created_at": segment.created_at or datetime.now(UTC)})
            for segment in segments
        ]
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_model_output_segments),
                [segment.model_dump(mode="python") for segment in stored],
            )
        return stored

    def list_segments(self, model_output_id: str) -> list[ModelOutputSegment]:
        self._ensure_schema()
        statement = (
            select(aion_model_output_segments)
            .where(aion_model_output_segments.c.model_output_id == model_output_id)
            .where(aion_model_output_segments.c.deleted_at.is_(None))
            .order_by(aion_model_output_segments.c.segment_order.asc())
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ModelOutputSegment(**dict(row)) for row in rows]

    def save_validation(self, validation: StructuredOutputValidation) -> StructuredOutputValidation:
        self._ensure_schema()
        stored = validation.model_copy(
            update={"created_at": validation.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_structured_output_validations).values(
                    **stored.model_dump(mode="python")
                )
            )
        return stored

    def list_validations(self, model_output_id: str) -> list[StructuredOutputValidation]:
        self._ensure_schema()
        statement = select(aion_structured_output_validations).where(
            aion_structured_output_validations.c.model_output_id == model_output_id
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [StructuredOutputValidation(**dict(row)) for row in rows]

    def save_response_candidate(self, candidate: ResponseCandidate) -> ResponseCandidate:
        self._ensure_schema()
        stored = candidate.model_copy(
            update={"created_at": candidate.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_response_candidates).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_response_candidate(self, response_candidate_id: str) -> ResponseCandidate | None:
        self._ensure_schema()
        statement = select(aion_response_candidates).where(
            aion_response_candidates.c.response_candidate_id == response_candidate_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return ResponseCandidate(**dict(row)) if row is not None else None

    def list_response_candidates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ResponseCandidate]:
        self._ensure_schema()
        statement = (
            select(aion_response_candidates)
            .where(aion_response_candidates.c.deleted_at.is_(None))
            .order_by(aion_response_candidates.c.created_at.desc())
        )
        if status is not None:
            statement = statement.where(aion_response_candidates.c.status == status)
        if trace_id is not None:
            statement = statement.where(aion_response_candidates.c.trace_id == trace_id)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            ResponseCandidate(**dict(row)) for row in rows if _candidate_scope_matches(row, scope)
        ]

    def update_response_candidate(self, candidate: ResponseCandidate) -> ResponseCandidate:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_response_candidates)
                .where(
                    aion_response_candidates.c.response_candidate_id
                    == candidate.response_candidate_id
                )
                .values(**candidate.model_dump(mode="python"))
            )
        return candidate

    def save_tool_intents(self, intents: list[ToolIntentCandidate]) -> list[ToolIntentCandidate]:
        self._ensure_schema()
        if not intents:
            return []
        stored = [
            intent.model_copy(update={"created_at": intent.created_at or datetime.now(UTC)})
            for intent in intents
        ]
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_tool_intent_candidates),
                [intent.model_dump(mode="python") for intent in stored],
            )
        return stored

    def get_tool_intent(self, tool_intent_id: str) -> ToolIntentCandidate | None:
        self._ensure_schema()
        statement = select(aion_tool_intent_candidates).where(
            aion_tool_intent_candidates.c.tool_intent_id == tool_intent_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return ToolIntentCandidate(**dict(row)) if row is not None else None

    def list_tool_intents(
        self,
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ToolIntentCandidate]:
        self._ensure_schema()
        statement = select(aion_tool_intent_candidates).order_by(
            aion_tool_intent_candidates.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_tool_intent_candidates.c.status == status)
        if trace_id is not None:
            statement = statement.where(aion_tool_intent_candidates.c.trace_id == trace_id)
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [ToolIntentCandidate(**dict(row)) for row in rows]

    def update_tool_intent(self, intent: ToolIntentCandidate) -> ToolIntentCandidate:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_tool_intent_candidates)
                .where(aion_tool_intent_candidates.c.tool_intent_id == intent.tool_intent_id)
                .values(**intent.model_dump(mode="python"))
            )
        return intent

    def save_governance_run(self, run: OutputGovernanceRun) -> OutputGovernanceRun:
        self._ensure_schema()
        stored = run.model_copy(
            update={
                "created_at": run.created_at or datetime.now(UTC),
                "completed_at": run.completed_at or datetime.now(UTC),
            }
        )
        values = _governance_values(stored)
        with self._engine.begin() as connection:
            connection.execute(insert(aion_output_governance_runs).values(**values))
        return stored

    def get_governance_run(self, output_governance_id: str) -> OutputGovernanceRun | None:
        self._ensure_schema()
        statement = select(aion_output_governance_runs).where(
            aion_output_governance_runs.c.output_governance_id == output_governance_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return self._row_to_governance(row) if row is not None else None

    def list_governance_runs(self, model_output_id: str) -> list[OutputGovernanceRun]:
        self._ensure_schema()
        statement = select(aion_output_governance_runs).where(
            aion_output_governance_runs.c.model_output_id == model_output_id
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [run for row in rows if (run := self._row_to_governance(row)) is not None]

    def query(self, query: ModelOutputQuery) -> ModelOutputQueryResult:
        outputs = self.list_outputs(query)
        output_ids = [output.model_output_id for output in outputs]
        segments = [
            segment for output_id in output_ids for segment in self.list_segments(output_id)
        ]
        candidates = [
            candidate
            for candidate in self.list_response_candidates(query.scope, trace_id=query.trace_id)
            if candidate.model_output_id in output_ids
        ]
        intents = [
            intent
            for intent in self.list_tool_intents(trace_id=query.trace_id)
            if intent.model_output_id in output_ids
        ]
        runs = [run for output_id in output_ids for run in self.list_governance_runs(output_id)]
        return ModelOutputQueryResult(
            outputs=outputs,
            segments=segments,
            response_candidates=candidates,
            tool_intents=intents,
            governance_runs=runs,
            total_count=len(outputs),
            constraints=["redacted_outputs_only"],
            metadata={"source": "model_output_repository"},
        )

    def _row_to_governance(self, row: RowMapping | None) -> OutputGovernanceRun | None:
        if row is None:
            return None
        values = dict(row)
        model_output_id = values["model_output_id"]
        return OutputGovernanceRun(
            output_governance_id=values["output_governance_id"],
            trace_id=values["trace_id"],
            model_output_id=model_output_id,
            status=values["status"],
            owner_scope=values["owner_scope"],
            parsed_segments=[
                segment
                for segment in self.list_segments(model_output_id)
                if segment.output_segment_id in values["parsed_segment_ids"]
            ],
            response_candidates=[
                candidate
                for candidate in self.list_response_candidates(values["owner_scope"], limit=500)
                if candidate.response_candidate_id in values["response_candidate_ids"]
            ],
            tool_intents=[
                intent
                for intent in self.list_tool_intents(limit=500)
                if intent.tool_intent_id in values["tool_intent_ids"]
            ],
            structured_validations=[
                validation
                for validation in self.list_validations(model_output_id)
                if validation.structured_validation_id in values["structured_validation_ids"]
            ],
            blocked=values["blocked"],
            issues=values["issues"],
            constraints=values["constraints"],
            score=values["score"],
            result=values["result"],
            created_by=values["created_by"],
            created_at=values["created_at"],
            completed_at=values["completed_at"],
        )

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            model_output_metadata.create_all(self._engine)
        self._schema_ready = True


def _governance_values(run: OutputGovernanceRun) -> dict[str, Any]:
    return {
        "output_governance_id": run.output_governance_id,
        "trace_id": run.trace_id,
        "model_output_id": run.model_output_id,
        "status": run.status,
        "owner_scope": run.owner_scope,
        "parsed_segment_ids": [item.output_segment_id for item in run.parsed_segments],
        "response_candidate_ids": [item.response_candidate_id for item in run.response_candidates],
        "tool_intent_ids": [item.tool_intent_id for item in run.tool_intents],
        "structured_validation_ids": [
            item.structured_validation_id for item in run.structured_validations
        ],
        "blocked": run.blocked,
        "issues": run.issues,
        "constraints": run.constraints,
        "score": run.score,
        "result": run.result,
        "created_by": run.created_by,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


def _candidate_scope_matches(row: RowMapping, scope: list[str]) -> bool:
    metadata = row.get("metadata", {})
    owner_scope = metadata.get("owner_scope") if isinstance(metadata, dict) else None
    if not owner_scope:
        return True
    return bool(set(owner_scope).intersection(scope))


__all__ = ["ModelOutputRepository"]
