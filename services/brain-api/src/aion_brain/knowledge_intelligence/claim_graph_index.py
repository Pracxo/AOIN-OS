"""Deterministic indexes and bounded exact queries for the claim graph."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_claim_graph import (
    CLAIM_GRAPH_INDEX_SCHEMA_VERSION,
    CLAIM_GRAPH_QUERY_SCHEMA_VERSION,
    MAXIMUM_QUERY_RESULTS,
    ClaimEvidenceBinding,
    ClaimGraphRecordEnvelope,
    ClaimRelationEdge,
    ClaimRelationType,
    StructuralConflictCandidate,
    UnverifiedClaimAssertion,
)
from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ensure_utc,
    fingerprint_payload,
    validate_hex64,
    validate_safe_identifier,
)

ClaimGraphQueryKind = Literal[
    "record_id",
    "claim_id",
    "claim_identity_fingerprint",
    "subject_id",
    "predicate",
    "subject_and_predicate",
    "source_registry_record_id",
    "citation_id",
    "lineage_group_id",
    "jurisdiction_id",
    "version_target_id",
    "valid_time_range",
    "relation_type",
    "structural_conflict_candidate_for_claim",
]


class ClaimGraphIndexEntry(BaseModel):
    """Immutable index entry exposing only safe IDs."""

    model_config = FROZEN_MODEL_CONFIG

    key: str
    record_ids: tuple[str, ...]

    @field_validator("key")
    @classmethod
    def key_is_safe(cls, value: str) -> str:
        if len(value) == 64:
            return validate_hex64(value, "claim graph index key")
        return validate_safe_identifier(value, "claim graph index key")

    @field_validator("record_ids")
    @classmethod
    def record_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate index entry rejected")
        for item in value:
            validate_safe_identifier(item, "claim graph indexed record_id")
        return value


class ClaimGraphIndex(BaseModel):
    """Immutable deterministic claim-graph index."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-index/v1"] = (
        CLAIM_GRAPH_INDEX_SCHEMA_VERSION
    )
    record_ids: tuple[str, ...]
    records_by_id: dict[str, tuple[str, ...]]
    claims_by_claim_id: dict[str, tuple[str, ...]]
    claims_by_identity_fingerprint: dict[str, tuple[str, ...]]
    claims_by_subject_id: dict[str, tuple[str, ...]]
    claims_by_predicate: dict[str, tuple[str, ...]]
    claims_by_subject_and_predicate: dict[str, tuple[str, ...]]
    bindings_by_claim_id: dict[str, tuple[str, ...]]
    bindings_by_source_registry_record_id: dict[str, tuple[str, ...]]
    bindings_by_citation_id: dict[str, tuple[str, ...]]
    bindings_by_lineage_group_id: dict[str, tuple[str, ...]]
    claims_by_jurisdiction_id: dict[str, tuple[str, ...]]
    claims_by_version_target_id: dict[str, tuple[str, ...]]
    claims_by_valid_time_boundary: dict[str, tuple[str, ...]]
    relations_by_source_claim: dict[str, tuple[str, ...]]
    relations_by_target_claim: dict[str, tuple[str, ...]]
    relations_by_type: dict[str, tuple[str, ...]]
    structural_conflict_candidates_by_claim: dict[str, tuple[str, ...]]
    index_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("record_ids")
    @classmethod
    def record_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate indexed record IDs rejected")
        for item in value:
            validate_safe_identifier(item, "claim graph record_id")
        return value

    @field_validator("index_fingerprint")
    @classmethod
    def index_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph index fingerprint")

    @model_validator(mode="after")
    def index_references_existing_records(self) -> Self:
        allowed = set(self.record_ids)
        for index_map in (
            self.records_by_id,
            self.claims_by_claim_id,
            self.claims_by_identity_fingerprint,
            self.claims_by_subject_id,
            self.claims_by_predicate,
            self.claims_by_subject_and_predicate,
            self.bindings_by_claim_id,
            self.bindings_by_source_registry_record_id,
            self.bindings_by_citation_id,
            self.bindings_by_lineage_group_id,
            self.claims_by_jurisdiction_id,
            self.claims_by_version_target_id,
            self.claims_by_valid_time_boundary,
            self.relations_by_source_claim,
            self.relations_by_target_claim,
            self.relations_by_type,
            self.structural_conflict_candidates_by_claim,
        ):
            for values in index_map.values():
                if len(set(values)) != len(values):
                    raise ValueError("duplicate index entry rejected")
                if set(values) - allowed:
                    raise ValueError("index references missing record")
        return self


class ClaimGraphQuery(BaseModel):
    """Bounded exact claim-graph query."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-query/v1"] = (
        CLAIM_GRAPH_QUERY_SCHEMA_VERSION
    )
    query_id: str
    query_kind: ClaimGraphQueryKind
    value: str | None = None
    secondary_value: str | None = None
    relation_type: ClaimRelationType | None = None
    valid_time_start: datetime | None = None
    valid_time_end: datetime | None = None
    limit: int = Field(default=100, ge=1, le=MAXIMUM_QUERY_RESULTS)
    runtime_effect: Literal[False] = False

    @field_validator("query_id")
    @classmethod
    def query_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph query_id")

    @field_validator("value", "secondary_value")
    @classmethod
    def values_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) == 64:
            return validate_hex64(value, "claim graph query value")
        return validate_safe_identifier(value, "claim graph query value")

    @field_validator("valid_time_start", "valid_time_end")
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return ensure_utc(value, "claim graph query time")
        return value

    @model_validator(mode="after")
    def query_shape_matches_kind(self) -> Self:
        if self.query_kind == "subject_and_predicate":
            if self.value is None or self.secondary_value is None:
                raise ValueError("subject_and_predicate query requires two values")
            return self
        if self.query_kind == "valid_time_range":
            if self.valid_time_start is None or self.valid_time_end is None:
                raise ValueError("valid_time_range query requires start and end")
            if self.valid_time_end < self.valid_time_start:
                raise ValueError("valid_time_end must not precede valid_time_start")
            return self
        if self.query_kind == "relation_type":
            if self.relation_type is None:
                raise ValueError("relation_type query requires relation_type")
            return self
        if self.value is None:
            raise ValueError("exact claim graph query requires value")
        return self


class ClaimGraphQueryResult(BaseModel):
    """Deterministic exact query result."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-query/v1"] = (
        CLAIM_GRAPH_QUERY_SCHEMA_VERSION
    )
    query: ClaimGraphQuery
    record_ids: tuple[str, ...]
    records: tuple[ClaimGraphRecordEnvelope, ...]
    result_count: int = Field(ge=0)
    truncated: bool
    query_fingerprint: str
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("record_ids")
    @classmethod
    def record_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            validate_safe_identifier(item, "claim graph query result record_id")
        return value

    @field_validator("query_fingerprint")
    @classmethod
    def query_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph query fingerprint")

    @model_validator(mode="after")
    def result_count_matches(self) -> Self:
        if self.result_count != len(self.records) or self.result_count != len(self.record_ids):
            raise ValueError("result_count must match returned records")
        return self


def build_claim_graph_index(records: tuple[ClaimGraphRecordEnvelope, ...]) -> ClaimGraphIndex:
    """Build deterministic exact-match indexes from validated records."""

    ordered = tuple(sorted(records, key=lambda item: item.sequence_number))
    indexes: dict[str, defaultdict[str, list[str]]] = {
        name: defaultdict(list)
        for name in (
            "records_by_id",
            "claims_by_claim_id",
            "claims_by_identity_fingerprint",
            "claims_by_subject_id",
            "claims_by_predicate",
            "claims_by_subject_and_predicate",
            "bindings_by_claim_id",
            "bindings_by_source_registry_record_id",
            "bindings_by_citation_id",
            "bindings_by_lineage_group_id",
            "claims_by_jurisdiction_id",
            "claims_by_version_target_id",
            "claims_by_valid_time_boundary",
            "relations_by_source_claim",
            "relations_by_target_claim",
            "relations_by_type",
            "structural_conflict_candidates_by_claim",
        )
    }
    for record in ordered:
        indexes["records_by_id"][record.record_id].append(record.record_id)
        payload = record.payload
        if isinstance(payload, UnverifiedClaimAssertion):
            indexes["claims_by_claim_id"][payload.claim_id].append(record.record_id)
            indexes["claims_by_identity_fingerprint"][payload.claim_identity_fingerprint].append(
                record.record_id
            )
            indexes["claims_by_subject_id"][payload.subject_id].append(record.record_id)
            indexes["claims_by_predicate"][payload.predicate].append(record.record_id)
            indexes["claims_by_subject_and_predicate"][
                f"{payload.subject_id}:{payload.predicate}"
            ].append(record.record_id)
            for jurisdiction in payload.scope.jurisdiction_scopes:
                indexes["claims_by_jurisdiction_id"][jurisdiction.jurisdiction_id].append(
                    record.record_id
                )
            for version in payload.scope.version_scopes:
                indexes["claims_by_version_target_id"][version.target_id].append(record.record_id)
            for interval in payload.scope.valid_time_intervals:
                if interval.start is not None:
                    indexes["claims_by_valid_time_boundary"][interval.start.isoformat()].append(
                        record.record_id
                    )
                if interval.end is not None:
                    indexes["claims_by_valid_time_boundary"][interval.end.isoformat()].append(
                        record.record_id
                    )
        elif isinstance(payload, ClaimEvidenceBinding):
            indexes["bindings_by_claim_id"][payload.claim_id].append(record.record_id)
            for source_id in payload.source_registry_record_ids:
                indexes["bindings_by_source_registry_record_id"][source_id].append(record.record_id)
            for citation_id in payload.citation_record_ids:
                indexes["bindings_by_citation_id"][citation_id].append(record.record_id)
            for lineage_group_id in payload.lineage_group_ids:
                indexes["bindings_by_lineage_group_id"][lineage_group_id].append(record.record_id)
        elif isinstance(payload, ClaimRelationEdge):
            indexes["relations_by_source_claim"][payload.source_claim_id].append(record.record_id)
            indexes["relations_by_target_claim"][payload.target_claim_id].append(record.record_id)
            indexes["relations_by_type"][payload.relation_type.value].append(record.record_id)
        elif isinstance(payload, StructuralConflictCandidate):
            indexes["structural_conflict_candidates_by_claim"][payload.left_claim_id].append(
                record.record_id
            )
            indexes["structural_conflict_candidates_by_claim"][payload.right_claim_id].append(
                record.record_id
            )

    frozen = {name: _freeze_index(index) for name, index in indexes.items()}
    index_payload = {
        "record_ids": [record.record_id for record in ordered],
        **frozen,
    }
    return ClaimGraphIndex(
        record_ids=tuple(record.record_id for record in ordered),
        records_by_id=frozen["records_by_id"],
        claims_by_claim_id=frozen["claims_by_claim_id"],
        claims_by_identity_fingerprint=frozen["claims_by_identity_fingerprint"],
        claims_by_subject_id=frozen["claims_by_subject_id"],
        claims_by_predicate=frozen["claims_by_predicate"],
        claims_by_subject_and_predicate=frozen["claims_by_subject_and_predicate"],
        bindings_by_claim_id=frozen["bindings_by_claim_id"],
        bindings_by_source_registry_record_id=frozen["bindings_by_source_registry_record_id"],
        bindings_by_citation_id=frozen["bindings_by_citation_id"],
        bindings_by_lineage_group_id=frozen["bindings_by_lineage_group_id"],
        claims_by_jurisdiction_id=frozen["claims_by_jurisdiction_id"],
        claims_by_version_target_id=frozen["claims_by_version_target_id"],
        claims_by_valid_time_boundary=frozen["claims_by_valid_time_boundary"],
        relations_by_source_claim=frozen["relations_by_source_claim"],
        relations_by_target_claim=frozen["relations_by_target_claim"],
        relations_by_type=frozen["relations_by_type"],
        structural_conflict_candidates_by_claim=frozen[
            "structural_conflict_candidates_by_claim"
        ],
        index_fingerprint=fingerprint_payload(index_payload),
    )


def query_claim_graph(
    records: tuple[ClaimGraphRecordEnvelope, ...],
    index: ClaimGraphIndex,
    query: ClaimGraphQuery,
) -> ClaimGraphQueryResult:
    """Run a bounded exact query and preserve graph-record order."""

    if query.query_kind == "record_id":
        result_ids = index.records_by_id.get(query.value or "", ())
    elif query.query_kind == "claim_id":
        result_ids = index.claims_by_claim_id.get(query.value or "", ())
    elif query.query_kind == "claim_identity_fingerprint":
        result_ids = index.claims_by_identity_fingerprint.get(query.value or "", ())
    elif query.query_kind == "subject_id":
        result_ids = index.claims_by_subject_id.get(query.value or "", ())
    elif query.query_kind == "predicate":
        result_ids = index.claims_by_predicate.get(query.value or "", ())
    elif query.query_kind == "subject_and_predicate":
        result_ids = index.claims_by_subject_and_predicate.get(
            f"{query.value}:{query.secondary_value}",
            (),
        )
    elif query.query_kind == "source_registry_record_id":
        result_ids = index.bindings_by_source_registry_record_id.get(query.value or "", ())
    elif query.query_kind == "citation_id":
        result_ids = index.bindings_by_citation_id.get(query.value or "", ())
    elif query.query_kind == "lineage_group_id":
        result_ids = index.bindings_by_lineage_group_id.get(query.value or "", ())
    elif query.query_kind == "jurisdiction_id":
        result_ids = index.claims_by_jurisdiction_id.get(query.value or "", ())
    elif query.query_kind == "version_target_id":
        result_ids = index.claims_by_version_target_id.get(query.value or "", ())
    elif query.query_kind == "valid_time_range":
        result_ids = _query_valid_time_range(records, query)
    elif query.query_kind == "relation_type":
        relation_type = query.relation_type.value if query.relation_type is not None else ""
        result_ids = index.relations_by_type.get(relation_type, ())
    else:
        result_ids = index.structural_conflict_candidates_by_claim.get(query.value or "", ())
    limited = result_ids[: query.limit]
    record_map = {record.record_id: record for record in records}
    result_records = tuple(record_map[record_id] for record_id in limited)
    payload = {
        "query": query.model_dump(mode="json"),
        "record_ids": limited,
        "truncated": len(result_ids) > len(limited),
    }
    return ClaimGraphQueryResult(
        query=query,
        record_ids=tuple(limited),
        records=result_records,
        result_count=len(limited),
        truncated=len(result_ids) > len(limited),
        query_fingerprint=fingerprint_payload(payload),
    )


def _query_valid_time_range(
    records: tuple[ClaimGraphRecordEnvelope, ...],
    query: ClaimGraphQuery,
) -> tuple[str, ...]:
    start = query.valid_time_start
    end = query.valid_time_end
    if start is None or end is None:
        return ()
    matches: list[str] = []
    for record in records:
        if not isinstance(record.payload, UnverifiedClaimAssertion):
            continue
        for interval in record.payload.scope.valid_time_intervals:
            if interval.end is not None and interval.end < start:
                continue
            if interval.start is not None and interval.start > end:
                continue
            matches.append(record.record_id)
            break
    return tuple(dict.fromkeys(matches))


def _freeze_index(values: defaultdict[str, list[str]]) -> dict[str, tuple[str, ...]]:
    return {key: tuple(dict.fromkeys(values[key])) for key in sorted(values)}


__all__ = [
    "ClaimGraphIndex",
    "ClaimGraphIndexEntry",
    "ClaimGraphQuery",
    "ClaimGraphQueryKind",
    "ClaimGraphQueryResult",
    "build_claim_graph_index",
    "query_claim_graph",
]
