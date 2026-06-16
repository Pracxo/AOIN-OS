"""Persistence for belief claims and truth maintenance."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
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

from aion_brain.contracts.beliefs import (
    BeliefClaim,
    BeliefClaimStatus,
    BeliefClaimType,
    BeliefContradiction,
    BeliefContradictionStatus,
    BeliefContradictionType,
    BeliefQuery,
    BeliefRelationType,
    BeliefRevision,
    BeliefSensitivity,
    BeliefSeverity,
    BeliefSourceType,
    BeliefSupport,
    BeliefSupportType,
    TruthMaintenanceRun,
    TruthMaintenanceStatus,
)

belief_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_belief_claims = Table(
    "aion_belief_claims",
    belief_metadata,
    Column("claim_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("claim_text", Text, nullable=False),
    Column("normalized_claim", Text, nullable=False),
    Column("claim_hash", Text, nullable=False),
    Column("claim_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("memory_refs", json_payload_type, nullable=False),
    Column("graph_refs", json_payload_type, nullable=False),
    Column("response_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("valid_from", DateTime(timezone=True), nullable=True),
    Column("valid_to", DateTime(timezone=True), nullable=True),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_belief_claims_trace_id", "trace_id"),
    Index("ix_aion_belief_claims_actor_id", "actor_id"),
    Index("ix_aion_belief_claims_workspace_id", "workspace_id"),
    Index("ix_aion_belief_claims_claim_hash", "claim_hash"),
    Index("ix_aion_belief_claims_claim_type", "claim_type"),
    Index("ix_aion_belief_claims_status", "status"),
    Index("ix_aion_belief_claims_confidence", "confidence"),
    Index("ix_aion_belief_claims_sensitivity", "sensitivity"),
    Index("ix_aion_belief_claims_source_type", "source_type"),
    Index("ix_aion_belief_claims_source_id", "source_id"),
    Index("ix_aion_belief_claims_observed_at", "observed_at"),
    Index("ix_aion_belief_claims_created_at", "created_at"),
    Index("ix_aion_belief_claims_deleted_at", "deleted_at"),
)

aion_belief_supports = Table(
    "aion_belief_supports",
    belief_metadata,
    Column("support_id", Text, primary_key=True),
    Column("claim_id", Text, ForeignKey("aion_belief_claims.claim_id"), nullable=False),
    Column("support_type", Text, nullable=False),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("relation_type", Text, nullable=False),
    Column("strength", Float, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_belief_supports_claim_id", "claim_id"),
    Index("ix_aion_belief_supports_support_type", "support_type"),
    Index("ix_aion_belief_supports_source_type", "source_type"),
    Index("ix_aion_belief_supports_source_id", "source_id"),
    Index("ix_aion_belief_supports_relation_type", "relation_type"),
    Index("ix_aion_belief_supports_strength", "strength"),
    Index("ix_aion_belief_supports_confidence", "confidence"),
    Index("ix_aion_belief_supports_deleted_at", "deleted_at"),
    Index("ix_aion_belief_supports_created_at", "created_at"),
)

aion_belief_contradictions = Table(
    "aion_belief_contradictions",
    belief_metadata,
    Column("contradiction_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("claim_id", Text, ForeignKey("aion_belief_claims.claim_id"), nullable=False),
    Column("contradicting_claim_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("contradiction_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_belief_contradictions_trace_id", "trace_id"),
    Index("ix_aion_belief_contradictions_claim_id", "claim_id"),
    Index("ix_aion_belief_contradictions_contradicting_claim_id", "contradicting_claim_id"),
    Index("ix_aion_belief_contradictions_source_type", "source_type"),
    Index("ix_aion_belief_contradictions_source_id", "source_id"),
    Index("ix_aion_belief_contradictions_contradiction_type", "contradiction_type"),
    Index("ix_aion_belief_contradictions_severity", "severity"),
    Index("ix_aion_belief_contradictions_status", "status"),
    Index("ix_aion_belief_contradictions_created_at", "created_at"),
)

aion_belief_revisions = Table(
    "aion_belief_revisions",
    belief_metadata,
    Column("revision_id", Text, primary_key=True),
    Column("claim_id", Text, ForeignKey("aion_belief_claims.claim_id"), nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("from_status", Text, nullable=True),
    Column("to_status", Text, nullable=False),
    Column("previous_confidence", Float, nullable=True),
    Column("new_confidence", Float, nullable=False),
    Column("reason", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_belief_revisions_claim_id", "claim_id"),
    Index("ix_aion_belief_revisions_trace_id", "trace_id"),
    Index("ix_aion_belief_revisions_from_status", "from_status"),
    Index("ix_aion_belief_revisions_to_status", "to_status"),
    Index("ix_aion_belief_revisions_new_confidence", "new_confidence"),
    Index("ix_aion_belief_revisions_created_at", "created_at"),
)

aion_truth_maintenance_runs = Table(
    "aion_truth_maintenance_runs",
    belief_metadata,
    Column("truth_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input_claim_ids", json_payload_type, nullable=False),
    Column("revised_claim_ids", json_payload_type, nullable=False),
    Column("contradiction_ids", json_payload_type, nullable=False),
    Column("stale_claim_ids", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_truth_maintenance_runs_trace_id", "trace_id"),
    Index("ix_aion_truth_maintenance_runs_actor_id", "actor_id"),
    Index("ix_aion_truth_maintenance_runs_workspace_id", "workspace_id"),
    Index("ix_aion_truth_maintenance_runs_status", "status"),
    Index("ix_aion_truth_maintenance_runs_created_at", "created_at"),
)


class BeliefRepository:
    """Repository for claim, support, contradiction, and truth-maintenance ledgers."""

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

    def save_claim(self, claim: BeliefClaim) -> BeliefClaim:
        self._ensure_schema()
        values = claim.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_belief_claims.c.claim_id).where(
                    aion_belief_claims.c.claim_id == claim.claim_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_belief_claims).values(**values))
            else:
                connection.execute(
                    update(aion_belief_claims)
                    .where(aion_belief_claims.c.claim_id == claim.claim_id)
                    .values(**values)
                )
        return claim

    def get_claim(self, claim_id: str) -> BeliefClaim | None:
        self._ensure_schema()
        row = self._first(
            select(aion_belief_claims).where(aion_belief_claims.c.claim_id == claim_id)
        )
        return _row_to_claim(row) if row is not None else None

    def find_duplicate(
        self,
        claim_hash: str,
        source_type: str,
        source_id: str | None,
    ) -> BeliefClaim | None:
        self._ensure_schema()
        statement = select(aion_belief_claims).where(
            aion_belief_claims.c.claim_hash == claim_hash,
            aion_belief_claims.c.source_type == source_type,
            aion_belief_claims.c.deleted_at.is_(None),
        )
        if source_id is None:
            statement = statement.where(aion_belief_claims.c.source_id.is_(None))
        else:
            statement = statement.where(aion_belief_claims.c.source_id == source_id)
        row = self._first(statement)
        return _row_to_claim(row) if row is not None else None

    def query_claims(self, query: BeliefQuery) -> list[BeliefClaim]:
        self._ensure_schema()
        statement = select(aion_belief_claims).order_by(
            aion_belief_claims.c.confidence.desc(),
            aion_belief_claims.c.updated_at.desc(),
        )
        if not query.include_deleted:
            statement = statement.where(aion_belief_claims.c.deleted_at.is_(None))
        if not query.include_stale:
            statement = statement.where(aion_belief_claims.c.status != "stale")
        if query.claim_types:
            statement = statement.where(aion_belief_claims.c.claim_type.in_(query.claim_types))
        if query.statuses:
            statement = statement.where(aion_belief_claims.c.status.in_(query.statuses))
        if query.source_types:
            statement = statement.where(aion_belief_claims.c.source_type.in_(query.source_types))
        if query.min_confidence is not None:
            statement = statement.where(aion_belief_claims.c.confidence >= query.min_confidence)
        rows = self._list(statement.limit(query.limit * 3))
        claims = [
            claim
            for claim in (_row_to_claim(row) for row in rows)
            if _in_scope(claim.owner_scope, query.scope)
        ]
        if query.query:
            needle = query.query.lower().strip()
            claims = [
                claim
                for claim in claims
                if needle in claim.claim_text.lower() or needle in claim.normalized_claim
            ]
        if query.evidence_refs:
            refs = set(query.evidence_refs)
            claims = [claim for claim in claims if refs.intersection(claim.evidence_refs)]
        return claims[: query.limit]

    def list_claims_by_ids(self, claim_ids: list[str]) -> list[BeliefClaim]:
        self._ensure_schema()
        if not claim_ids:
            return []
        statement = select(aion_belief_claims).where(aion_belief_claims.c.claim_id.in_(claim_ids))
        return [_row_to_claim(row) for row in self._list(statement)]

    def save_support(self, support: BeliefSupport) -> BeliefSupport:
        self._ensure_schema()
        values = support.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_belief_supports.c.support_id).where(
                    aion_belief_supports.c.support_id == support.support_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_belief_supports).values(**values))
            else:
                connection.execute(
                    update(aion_belief_supports)
                    .where(aion_belief_supports.c.support_id == support.support_id)
                    .values(**values)
                )
        return support

    def get_support(self, support_id: str) -> BeliefSupport | None:
        self._ensure_schema()
        row = self._first(
            select(aion_belief_supports).where(aion_belief_supports.c.support_id == support_id)
        )
        return _row_to_support(row) if row is not None else None

    def list_supports(self, claim_id: str, include_deleted: bool = False) -> list[BeliefSupport]:
        self._ensure_schema()
        statement = (
            select(aion_belief_supports)
            .where(aion_belief_supports.c.claim_id == claim_id)
            .order_by(aion_belief_supports.c.created_at)
        )
        if not include_deleted:
            statement = statement.where(aion_belief_supports.c.deleted_at.is_(None))
        return [_row_to_support(row) for row in self._list(statement)]

    def save_contradiction(self, contradiction: BeliefContradiction) -> BeliefContradiction:
        self._ensure_schema()
        values = contradiction.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_belief_contradictions.c.contradiction_id).where(
                    aion_belief_contradictions.c.contradiction_id == contradiction.contradiction_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_belief_contradictions).values(**values))
            else:
                connection.execute(
                    update(aion_belief_contradictions)
                    .where(
                        aion_belief_contradictions.c.contradiction_id
                        == contradiction.contradiction_id
                    )
                    .values(**values)
                )
        return contradiction

    def get_contradiction(self, contradiction_id: str) -> BeliefContradiction | None:
        self._ensure_schema()
        row = self._first(
            select(aion_belief_contradictions).where(
                aion_belief_contradictions.c.contradiction_id == contradiction_id
            )
        )
        return _row_to_contradiction(row) if row is not None else None

    def list_contradictions(
        self,
        *,
        claim_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[BeliefContradiction]:
        self._ensure_schema()
        statement = select(aion_belief_contradictions).order_by(
            aion_belief_contradictions.c.created_at.desc()
        )
        if claim_id is not None:
            statement = statement.where(aion_belief_contradictions.c.claim_id == claim_id)
        if status is not None:
            statement = statement.where(aion_belief_contradictions.c.status == status)
        if severity is not None:
            statement = statement.where(aion_belief_contradictions.c.severity == severity)
        return [_row_to_contradiction(row) for row in self._list(statement.limit(limit))]

    def save_revision(self, revision: BeliefRevision) -> BeliefRevision:
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_belief_revisions).values(**revision.model_dump(mode="python"))
            )
        return revision

    def save_truth_run(self, run: TruthMaintenanceRun) -> TruthMaintenanceRun:
        self._ensure_schema()
        values = run.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_truth_maintenance_runs.c.truth_run_id).where(
                    aion_truth_maintenance_runs.c.truth_run_id == run.truth_run_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_truth_maintenance_runs).values(**values))
            else:
                connection.execute(
                    update(aion_truth_maintenance_runs)
                    .where(aion_truth_maintenance_runs.c.truth_run_id == run.truth_run_id)
                    .values(**values)
                )
        return run

    def get_truth_run(self, truth_run_id: str) -> TruthMaintenanceRun | None:
        self._ensure_schema()
        row = self._first(
            select(aion_truth_maintenance_runs).where(
                aion_truth_maintenance_runs.c.truth_run_id == truth_run_id
            )
        )
        return _row_to_truth_run(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        belief_metadata.create_all(self._engine)
        self._schema_ready = True

    def _first(self, statement: Any) -> RowMapping | None:
        with self._engine.connect() as connection:
            return connection.execute(statement).mappings().first()

    def _list(self, statement: Any) -> list[RowMapping]:
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().all())


def _row_to_claim(row: RowMapping) -> BeliefClaim:
    return BeliefClaim(
        claim_id=str(row["claim_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        claim_text=str(row["claim_text"]),
        normalized_claim=str(row["normalized_claim"]),
        claim_hash=str(row["claim_hash"]),
        claim_type=cast(BeliefClaimType, str(row["claim_type"])),
        status=cast(BeliefClaimStatus, str(row["status"])),
        confidence=float(row["confidence"]),
        sensitivity=cast(BeliefSensitivity, str(row["sensitivity"])),
        owner_scope=_string_list(row["owner_scope"]),
        source_type=cast(BeliefSourceType, str(row["source_type"])),
        source_id=_optional_str(row["source_id"]),
        evidence_refs=_string_list(row["evidence_refs"]),
        memory_refs=_string_list(row["memory_refs"]),
        graph_refs=_string_list(row["graph_refs"]),
        response_refs=_string_list(row["response_refs"]),
        metadata=dict(row["metadata"]),
        valid_from=_optional_datetime(row["valid_from"]),
        valid_to=_optional_datetime(row["valid_to"]),
        observed_at=_datetime(row["observed_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_support(row: RowMapping) -> BeliefSupport:
    return BeliefSupport(
        support_id=str(row["support_id"]),
        claim_id=str(row["claim_id"]),
        support_type=cast(BeliefSupportType, str(row["support_type"])),
        source_type=cast(BeliefSourceType, str(row["source_type"])),
        source_id=str(row["source_id"]),
        relation_type=cast(BeliefRelationType, str(row["relation_type"])),
        strength=float(row["strength"]),
        confidence=float(row["confidence"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_contradiction(row: RowMapping) -> BeliefContradiction:
    return BeliefContradiction(
        contradiction_id=str(row["contradiction_id"]),
        trace_id=_optional_str(row["trace_id"]),
        claim_id=str(row["claim_id"]),
        contradicting_claim_id=_optional_str(row["contradicting_claim_id"]),
        source_type=cast(BeliefSourceType, str(row["source_type"])),
        source_id=str(row["source_id"]),
        contradiction_type=cast(BeliefContradictionType, str(row["contradiction_type"])),
        severity=cast(BeliefSeverity, str(row["severity"])),
        status=cast(BeliefContradictionStatus, str(row["status"])),
        reason=str(row["reason"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _row_to_truth_run(row: RowMapping) -> TruthMaintenanceRun:
    return TruthMaintenanceRun(
        truth_run_id=str(row["truth_run_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(TruthMaintenanceStatus, str(row["status"])),
        owner_scope=_string_list(row["owner_scope"]),
        input_claim_ids=_string_list(row["input_claim_ids"]),
        revised_claim_ids=_string_list(row["revised_claim_ids"]),
        contradiction_ids=_string_list(row["contradiction_ids"]),
        stale_claim_ids=_string_list(row["stale_claim_ids"]),
        result=dict(row["result"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    raise TypeError("expected datetime")


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return not owner_scope or bool(set(owner_scope) & set(requested_scope))
