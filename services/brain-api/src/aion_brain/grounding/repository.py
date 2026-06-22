"""Persistent repository for grounding and citation records."""

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

from aion_brain.contracts.citations import (
    CitationRecord,
    CitationType,
    ResponseCitationMap,
    ResponseCitationMapStatus,
    UnsupportedStatement,
    UnsupportedStatementSeverity,
)
from aion_brain.contracts.grounding import (
    GroundingSensitivity,
    GroundingSource,
    GroundingSourceType,
    GroundingTrustLevel,
    GroundingVerificationRun,
    GroundingVerificationStatus,
    GroundingVerificationTargetType,
    SourceCoverageReport,
    SourceCoverageStatus,
)

grounding_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_grounding_sources = Table(
    "aion_grounding_sources",
    grounding_metadata,
    Column("grounding_source_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("trust_level", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("belief_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("entity_refs", json_payload_type, nullable=False),
    Column("provenance_refs", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_grounding_sources_trace_id", "trace_id"),
    Index("ix_aion_grounding_sources_source_type", "source_type"),
    Index("ix_aion_grounding_sources_source_id", "source_id"),
    Index("ix_aion_grounding_sources_content_hash", "content_hash"),
    Index("ix_aion_grounding_sources_sensitivity", "sensitivity"),
    Index("ix_aion_grounding_sources_trust_level", "trust_level"),
    Index("ix_aion_grounding_sources_created_at", "created_at"),
    Index("ix_aion_grounding_sources_deleted_at", "deleted_at"),
)

aion_citation_records = Table(
    "aion_citation_records",
    grounding_metadata,
    Column("citation_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("response_id", Text, nullable=True),
    Column("explanation_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("grounding_source_id", Text, nullable=True),
    Column("citation_type", Text, nullable=False),
    Column("label", Text, nullable=False),
    Column("quote", Text, nullable=True),
    Column("start_char", Integer, nullable=True),
    Column("end_char", Integer, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("verified", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_citation_records_trace_id", "trace_id"),
    Index("ix_aion_citation_records_response_id", "response_id"),
    Index("ix_aion_citation_records_explanation_id", "explanation_id"),
    Index("ix_aion_citation_records_source_type", "source_type"),
    Index("ix_aion_citation_records_source_id", "source_id"),
    Index("ix_aion_citation_records_citation_type", "citation_type"),
    Index("ix_aion_citation_records_confidence", "confidence"),
    Index("ix_aion_citation_records_verified", "verified"),
    Index("ix_aion_citation_records_created_at", "created_at"),
    Index("ix_aion_citation_records_deleted_at", "deleted_at"),
)

aion_response_citation_maps = Table(
    "aion_response_citation_maps",
    grounding_metadata,
    Column("citation_map_id", Text, primary_key=True),
    Column("response_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("grounded", Boolean, nullable=False),
    Column("citation_ids", json_payload_type, nullable=False),
    Column("unsupported_statement_ids", json_payload_type, nullable=False),
    Column("coverage_score", Float, nullable=False),
    Column("required_source_types", json_payload_type, nullable=False),
    Column("missing_source_types", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_response_citation_maps_response_id", "response_id"),
    Index("ix_aion_response_citation_maps_trace_id", "trace_id"),
    Index("ix_aion_response_citation_maps_status", "status"),
    Index("ix_aion_response_citation_maps_grounded", "grounded"),
    Index("ix_aion_response_citation_maps_coverage_score", "coverage_score"),
    Index("ix_aion_response_citation_maps_created_at", "created_at"),
)

aion_unsupported_statements = Table(
    "aion_unsupported_statements",
    grounding_metadata,
    Column("unsupported_statement_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("response_id", Text, nullable=True),
    Column("explanation_id", Text, nullable=True),
    Column("statement_text", Text, nullable=False),
    Column("statement_hash", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("required_support", json_payload_type, nullable=False),
    Column("candidate_source_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_unsupported_statements_trace_id", "trace_id"),
    Index("ix_aion_unsupported_statements_response_id", "response_id"),
    Index("ix_aion_unsupported_statements_explanation_id", "explanation_id"),
    Index("ix_aion_unsupported_statements_statement_hash", "statement_hash"),
    Index("ix_aion_unsupported_statements_severity", "severity"),
    Index("ix_aion_unsupported_statements_created_at", "created_at"),
    Index("ix_aion_unsupported_statements_resolved_at", "resolved_at"),
)

aion_grounding_verification_runs = Table(
    "aion_grounding_verification_runs",
    grounding_metadata,
    Column("grounding_verification_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("response_id", Text, nullable=True),
    Column("explanation_id", Text, nullable=True),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("grounded", Boolean, nullable=False),
    Column("checked_statement_count", Integer, nullable=False),
    Column("supported_statement_count", Integer, nullable=False),
    Column("unsupported_statement_count", Integer, nullable=False),
    Column("citation_count", Integer, nullable=False),
    Column("coverage_score", Float, nullable=False),
    Column("issues", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_grounding_verification_runs_trace_id", "trace_id"),
    Index("ix_aion_grounding_verification_runs_response_id", "response_id"),
    Index("ix_aion_grounding_verification_runs_explanation_id", "explanation_id"),
    Index("ix_aion_grounding_verification_runs_target_type", "target_type"),
    Index("ix_aion_grounding_verification_runs_target_id", "target_id"),
    Index("ix_aion_grounding_verification_runs_status", "status"),
    Index("ix_aion_grounding_verification_runs_grounded", "grounded"),
    Index("ix_aion_grounding_verification_runs_coverage_score", "coverage_score"),
    Index("ix_aion_grounding_verification_runs_created_at", "created_at"),
)

aion_source_coverage_reports = Table(
    "aion_source_coverage_reports",
    grounding_metadata,
    Column("source_coverage_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("response_id", Text, nullable=True),
    Column("explanation_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_counts", json_payload_type, nullable=False),
    Column("required_source_types", json_payload_type, nullable=False),
    Column("missing_source_types", json_payload_type, nullable=False),
    Column("weak_source_refs", json_payload_type, nullable=False),
    Column("strong_source_refs", json_payload_type, nullable=False),
    Column("coverage_score", Float, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_source_coverage_reports_trace_id", "trace_id"),
    Index("ix_aion_source_coverage_reports_response_id", "response_id"),
    Index("ix_aion_source_coverage_reports_explanation_id", "explanation_id"),
    Index("ix_aion_source_coverage_reports_status", "status"),
    Index("ix_aion_source_coverage_reports_coverage_score", "coverage_score"),
    Index("ix_aion_source_coverage_reports_created_at", "created_at"),
)


class GroundingRepository:
    """Repository for Grounding Manager records."""

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

    def save_source(self, source: GroundingSource) -> GroundingSource:
        self._ensure_schema()
        stored = source.model_copy(update={"created_at": source.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_grounding_sources).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_source(self, grounding_source_id: str) -> GroundingSource | None:
        self._ensure_schema()
        statement = select(aion_grounding_sources).where(
            aion_grounding_sources.c.grounding_source_id == grounding_source_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_source(row) if row is not None else None

    def list_sources(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        source_type: str | None = None,
        trust_level: str | None = None,
        include_deleted: bool = False,
        limit: int = 500,
    ) -> list[GroundingSource]:
        self._ensure_schema()
        statement = select(aion_grounding_sources).order_by(
            aion_grounding_sources.c.created_at.desc()
        )
        if trace_id is not None:
            statement = statement.where(aion_grounding_sources.c.trace_id == trace_id)
        if source_type is not None:
            statement = statement.where(aion_grounding_sources.c.source_type == source_type)
        if trust_level is not None:
            statement = statement.where(aion_grounding_sources.c.trust_level == trust_level)
        if not include_deleted:
            statement = statement.where(aion_grounding_sources.c.deleted_at.is_(None))
        statement = statement.limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            _row_to_source(row) for row in rows if _scope_matches(list(row["owner_scope"]), scope)
        ]

    def save_citation(self, citation: CitationRecord) -> CitationRecord:
        self._ensure_schema()
        stored = citation.model_copy(
            update={"created_at": citation.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_citation_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_citations(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
        source_id: str | None = None,
        trace_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[CitationRecord]:
        self._ensure_schema()
        statement = select(aion_citation_records).order_by(
            aion_citation_records.c.created_at.desc()
        )
        if response_id is not None:
            statement = statement.where(aion_citation_records.c.response_id == response_id)
        if explanation_id is not None:
            statement = statement.where(aion_citation_records.c.explanation_id == explanation_id)
        if source_id is not None:
            statement = statement.where(aion_citation_records.c.source_id == source_id)
        if trace_id is not None:
            statement = statement.where(aion_citation_records.c.trace_id == trace_id)
        if not include_deleted:
            statement = statement.where(aion_citation_records.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [_row_to_citation(row) for row in rows]

    def soft_delete_citation(self, citation_id: str) -> bool:
        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_citation_records)
                .where(
                    aion_citation_records.c.citation_id == citation_id,
                    aion_citation_records.c.deleted_at.is_(None),
                )
                .values(deleted_at=datetime.now(UTC))
            )
        return result.rowcount == 1

    def save_citation_map(self, citation_map: ResponseCitationMap) -> ResponseCitationMap:
        self._ensure_schema()
        stored = citation_map.model_copy(
            update={"created_at": citation_map.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_response_citation_maps).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_citation_map(self, citation_map_id: str) -> ResponseCitationMap | None:
        self._ensure_schema()
        statement = select(aion_response_citation_maps).where(
            aion_response_citation_maps.c.citation_map_id == citation_map_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_citation_map(row) if row is not None else None

    def latest_citation_map(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
    ) -> ResponseCitationMap | None:
        self._ensure_schema()
        statement = select(aion_response_citation_maps).order_by(
            aion_response_citation_maps.c.created_at.desc()
        )
        if response_id is not None:
            statement = statement.where(aion_response_citation_maps.c.response_id == response_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(25)).mappings().all()
        maps = [_row_to_citation_map(row) for row in rows]
        if explanation_id is None:
            return maps[0] if maps else None
        for citation_map in maps:
            if citation_map.metadata.get("explanation_id") == explanation_id:
                return citation_map
        return None

    def list_citation_maps(
        self,
        *,
        response_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ResponseCitationMap]:
        self._ensure_schema()
        statement = select(aion_response_citation_maps).order_by(
            aion_response_citation_maps.c.created_at.desc()
        )
        if response_id is not None:
            statement = statement.where(aion_response_citation_maps.c.response_id == response_id)
        if trace_id is not None:
            statement = statement.where(aion_response_citation_maps.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [_row_to_citation_map(row) for row in rows]

    def save_unsupported(self, statement: UnsupportedStatement) -> UnsupportedStatement:
        self._ensure_schema()
        stored = statement.model_copy(
            update={"created_at": statement.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_unsupported_statements).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_unsupported(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[UnsupportedStatement]:
        self._ensure_schema()
        statement = select(aion_unsupported_statements).where(
            aion_unsupported_statements.c.resolved_at.is_(None)
        )
        if response_id is not None:
            statement = statement.where(aion_unsupported_statements.c.response_id == response_id)
        if explanation_id is not None:
            statement = statement.where(
                aion_unsupported_statements.c.explanation_id == explanation_id
            )
        if trace_id is not None:
            statement = statement.where(aion_unsupported_statements.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    statement.order_by(aion_unsupported_statements.c.created_at.desc()).limit(limit)
                )
                .mappings()
                .all()
            )
        return [_row_to_unsupported(row) for row in rows]

    def save_verification_run(
        self,
        run: GroundingVerificationRun,
    ) -> GroundingVerificationRun:
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = run.model_copy(
            update={"created_at": run.created_at or now, "completed_at": run.completed_at or now}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_grounding_verification_runs).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_verification_run(
        self,
        grounding_verification_id: str,
    ) -> GroundingVerificationRun | None:
        self._ensure_schema()
        statement = select(aion_grounding_verification_runs).where(
            aion_grounding_verification_runs.c.grounding_verification_id
            == grounding_verification_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_verification(row) if row is not None else None

    def list_verification_runs(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[GroundingVerificationRun]:
        self._ensure_schema()
        statement = select(aion_grounding_verification_runs).order_by(
            aion_grounding_verification_runs.c.created_at.desc()
        )
        if response_id is not None:
            statement = statement.where(
                aion_grounding_verification_runs.c.response_id == response_id
            )
        if explanation_id is not None:
            statement = statement.where(
                aion_grounding_verification_runs.c.explanation_id == explanation_id
            )
        if trace_id is not None:
            statement = statement.where(aion_grounding_verification_runs.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [_row_to_verification(row) for row in rows]

    def save_coverage_report(self, report: SourceCoverageReport) -> SourceCoverageReport:
        self._ensure_schema()
        stored = report.model_copy(update={"created_at": report.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_source_coverage_reports).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_coverage_reports(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[SourceCoverageReport]:
        self._ensure_schema()
        statement = select(aion_source_coverage_reports).order_by(
            aion_source_coverage_reports.c.created_at.desc()
        )
        if response_id is not None:
            statement = statement.where(aion_source_coverage_reports.c.response_id == response_id)
        if explanation_id is not None:
            statement = statement.where(
                aion_source_coverage_reports.c.explanation_id == explanation_id
            )
        if trace_id is not None:
            statement = statement.where(aion_source_coverage_reports.c.trace_id == trace_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [_row_to_coverage(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        grounding_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_source(row: RowMapping) -> GroundingSource:
    return GroundingSource(
        grounding_source_id=str(row["grounding_source_id"]),
        trace_id=_optional_str(row["trace_id"]),
        source_type=cast(GroundingSourceType, str(row["source_type"])),
        source_id=str(row["source_id"]),
        title=str(row["title"]),
        summary=str(row["summary"]),
        content_hash=str(row["content_hash"]),
        sensitivity=cast(GroundingSensitivity, str(row["sensitivity"])),
        trust_level=cast(GroundingTrustLevel, str(row["trust_level"])),
        evidence_refs=list(row["evidence_refs"]),
        belief_refs=list(row["belief_refs"]),
        memory_refs=list(row["memory_refs"]),
        entity_refs=list(row["entity_refs"]),
        provenance_refs=list(row["provenance_refs"]),
        owner_scope=list(row["owner_scope"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_citation(row: RowMapping) -> CitationRecord:
    return CitationRecord(
        citation_id=str(row["citation_id"]),
        trace_id=_optional_str(row["trace_id"]),
        response_id=_optional_str(row["response_id"]),
        explanation_id=_optional_str(row["explanation_id"]),
        source_type=cast(GroundingSourceType, str(row["source_type"])),
        source_id=str(row["source_id"]),
        grounding_source_id=_optional_str(row["grounding_source_id"]),
        citation_type=cast(CitationType, str(row["citation_type"])),
        label=str(row["label"]),
        quote=_optional_str(row["quote"]),
        start_char=_optional_int(row["start_char"]),
        end_char=_optional_int(row["end_char"]),
        confidence=float(row["confidence"]),
        verified=bool(row["verified"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_citation_map(row: RowMapping) -> ResponseCitationMap:
    return ResponseCitationMap(
        citation_map_id=str(row["citation_map_id"]),
        response_id=str(row["response_id"]),
        trace_id=_optional_str(row["trace_id"]),
        status=cast(ResponseCitationMapStatus, str(row["status"])),
        grounded=bool(row["grounded"]),
        citation_ids=list(row["citation_ids"]),
        unsupported_statement_ids=list(row["unsupported_statement_ids"]),
        coverage_score=float(row["coverage_score"]),
        required_source_types=cast(list[GroundingSourceType], list(row["required_source_types"])),
        missing_source_types=cast(list[GroundingSourceType], list(row["missing_source_types"])),
        constraints=list(row["constraints"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _row_to_unsupported(row: RowMapping) -> UnsupportedStatement:
    return UnsupportedStatement(
        unsupported_statement_id=str(row["unsupported_statement_id"]),
        trace_id=_optional_str(row["trace_id"]),
        response_id=_optional_str(row["response_id"]),
        explanation_id=_optional_str(row["explanation_id"]),
        statement_text=str(row["statement_text"]),
        statement_hash=str(row["statement_hash"]),
        reason=str(row["reason"]),
        severity=cast(UnsupportedStatementSeverity, str(row["severity"])),
        required_support=list(row["required_support"]),
        candidate_source_refs=list(row["candidate_source_refs"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _row_to_verification(row: RowMapping) -> GroundingVerificationRun:
    return GroundingVerificationRun(
        grounding_verification_id=str(row["grounding_verification_id"]),
        trace_id=_optional_str(row["trace_id"]),
        response_id=_optional_str(row["response_id"]),
        explanation_id=_optional_str(row["explanation_id"]),
        target_type=cast(GroundingVerificationTargetType, str(row["target_type"])),
        target_id=_optional_str(row["target_id"]),
        status=cast(GroundingVerificationStatus, str(row["status"])),
        owner_scope=list(row["owner_scope"]),
        grounded=bool(row["grounded"]),
        checked_statement_count=int(row["checked_statement_count"]),
        supported_statement_count=int(row["supported_statement_count"]),
        unsupported_statement_count=int(row["unsupported_statement_count"]),
        citation_count=int(row["citation_count"]),
        coverage_score=float(row["coverage_score"]),
        issues=list(row["issues"]),
        result=dict(row["result"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _row_to_coverage(row: RowMapping) -> SourceCoverageReport:
    return SourceCoverageReport(
        source_coverage_id=str(row["source_coverage_id"]),
        trace_id=_optional_str(row["trace_id"]),
        response_id=_optional_str(row["response_id"]),
        explanation_id=_optional_str(row["explanation_id"]),
        status=cast(SourceCoverageStatus, str(row["status"])),
        owner_scope=list(row["owner_scope"]),
        source_counts={str(key): int(value) for key, value in dict(row["source_counts"]).items()},
        required_source_types=cast(list[GroundingSourceType], list(row["required_source_types"])),
        missing_source_types=cast(list[GroundingSourceType], list(row["missing_source_types"])),
        weak_source_refs=list(row["weak_source_refs"]),
        strong_source_refs=list(row["strong_source_refs"]),
        coverage_score=float(row["coverage_score"]),
        recommendations=list(row["recommendations"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


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


__all__ = [
    "GroundingRepository",
    "aion_citation_records",
    "aion_grounding_sources",
    "aion_grounding_verification_runs",
    "aion_response_citation_maps",
    "aion_source_coverage_reports",
    "aion_unsupported_statements",
    "grounding_metadata",
]
