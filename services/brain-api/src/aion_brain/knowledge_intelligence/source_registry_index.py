"""Deterministic indexes and bounded exact queries for the source registry."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ResearchSourceClass,
    ensure_utc,
    fingerprint_payload,
    validate_hex64,
    validate_safe_identifier,
)
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredCitationReference,
    RegisteredDeduplicationDecision,
    RegisteredPolicyDecision,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
)

SourceRegistryQueryKind = Literal[
    "record_id",
    "snapshot_fingerprint",
    "content_sha256",
    "provenance_fingerprint",
    "citation_id",
    "lineage_group_id",
    "source_class",
    "retrieval_time_range",
]


class SourceRegistryIndex(BaseModel):
    """Immutable deterministic source-registry index."""

    model_config = FROZEN_MODEL_CONFIG

    record_ids: tuple[str, ...]
    records_by_id: dict[str, tuple[str, ...]]
    records_by_snapshot_fingerprint: dict[str, tuple[str, ...]]
    records_by_content_sha256: dict[str, tuple[str, ...]]
    records_by_provenance_fingerprint: dict[str, tuple[str, ...]]
    records_by_citation_id: dict[str, tuple[str, ...]]
    records_by_lineage_group_id: dict[str, tuple[str, ...]]
    records_by_source_class: dict[str, tuple[str, ...]]
    records_by_retrieval_timestamp: dict[str, tuple[str, ...]]
    index_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("record_ids")
    @classmethod
    def record_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate indexed record IDs are rejected")
        for item in value:
            validate_safe_identifier(item, "indexed record_id")
        return value

    @field_validator("index_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry index fingerprint")

    @model_validator(mode="after")
    def index_references_existing_records(self) -> Self:
        allowed = set(self.record_ids)
        for index_map in (
            self.records_by_id,
            self.records_by_snapshot_fingerprint,
            self.records_by_content_sha256,
            self.records_by_provenance_fingerprint,
            self.records_by_citation_id,
            self.records_by_lineage_group_id,
            self.records_by_source_class,
            self.records_by_retrieval_timestamp,
        ):
            for values in index_map.values():
                if len(set(values)) != len(values):
                    raise ValueError("duplicate index entry rejected")
                if set(values) - allowed:
                    raise ValueError("index references missing record")
        return self


class SourceRegistryQuery(BaseModel):
    """Bounded exact source-registry query."""

    model_config = FROZEN_MODEL_CONFIG

    query_id: str
    query_kind: SourceRegistryQueryKind
    value: str | None = None
    source_class: ResearchSourceClass | None = None
    retrieval_start: datetime | None = None
    retrieval_end: datetime | None = None
    limit: int = Field(default=100, ge=1, le=100)
    runtime_effect: Literal[False] = False

    @field_validator("query_id")
    @classmethod
    def query_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry query_id")

    @field_validator("value")
    @classmethod
    def query_value_is_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) == 64:
            return validate_hex64(value, "source registry query value")
        return validate_safe_identifier(value, "source registry query value")

    @field_validator("retrieval_start", "retrieval_end")
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value, "source registry query timestamp")

    @model_validator(mode="after")
    def query_shape_matches_kind(self) -> Self:
        if self.query_kind == "source_class":
            if self.source_class is None:
                raise ValueError("source_class query requires source_class")
            return self
        if self.query_kind == "retrieval_time_range":
            if self.retrieval_start is None or self.retrieval_end is None:
                raise ValueError("time-range query requires start and end")
            if self.retrieval_end < self.retrieval_start:
                raise ValueError("retrieval_end must not precede retrieval_start")
            return self
        if self.value is None:
            raise ValueError("exact source registry query requires a value")
        return self


class SourceRegistryQueryResult(BaseModel):
    """Deterministic exact query result."""

    model_config = FROZEN_MODEL_CONFIG

    query: SourceRegistryQuery
    record_ids: tuple[str, ...]
    records: tuple[SourceRegistryRecordEnvelope, ...]
    result_count: int = Field(ge=0)
    truncated: bool
    query_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("record_ids")
    @classmethod
    def record_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            validate_safe_identifier(item, "query result record_id")
        return value

    @field_validator("query_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry query fingerprint")

    @model_validator(mode="after")
    def result_count_matches(self) -> Self:
        if self.result_count != len(self.records) or self.result_count != len(self.record_ids):
            raise ValueError("result_count must match returned records")
        return self


def build_source_registry_index(
    records: tuple[SourceRegistryRecordEnvelope, ...],
) -> SourceRegistryIndex:
    """Build deterministic exact-match indexes from validated records."""

    ordered = tuple(sorted(records, key=lambda item: item.sequence_number))
    by_id: dict[str, list[str]] = defaultdict(list)
    by_snapshot_fingerprint: dict[str, list[str]] = defaultdict(list)
    by_content_sha256: dict[str, list[str]] = defaultdict(list)
    by_provenance_fingerprint: dict[str, list[str]] = defaultdict(list)
    by_citation_id: dict[str, list[str]] = defaultdict(list)
    by_lineage_group_id: dict[str, list[str]] = defaultdict(list)
    by_source_class: dict[str, list[str]] = defaultdict(list)
    by_retrieval_timestamp: dict[str, list[str]] = defaultdict(list)

    for record in ordered:
        by_id[record.record_id].append(record.record_id)
        payload = record.payload
        if isinstance(payload, RegisteredSourceSnapshotDigest):
            by_snapshot_fingerprint[payload.snapshot_fingerprint].append(record.record_id)
            by_content_sha256[payload.content_sha256].append(record.record_id)
            by_source_class[payload.source_class].append(record.record_id)
            by_retrieval_timestamp[payload.retrieval_timestamp.isoformat()].append(
                record.record_id
            )
        elif isinstance(payload, RegisteredSourceProvenance):
            by_snapshot_fingerprint[payload.snapshot_fingerprint].append(record.record_id)
            by_content_sha256[payload.content_sha256].append(record.record_id)
            by_provenance_fingerprint[payload.provenance_fingerprint].append(record.record_id)
            by_source_class[payload.source_class].append(record.record_id)
            by_retrieval_timestamp[payload.retrieval_timestamp.isoformat()].append(
                record.record_id
            )
        elif isinstance(payload, RegisteredCitationReference):
            by_snapshot_fingerprint[payload.snapshot_fingerprint].append(record.record_id)
            by_content_sha256[payload.content_sha256].append(record.record_id)
            by_citation_id[payload.citation_id].append(record.record_id)
            by_retrieval_timestamp[payload.retrieval_timestamp.isoformat()].append(
                record.record_id
            )
        elif isinstance(payload, RegisteredSourceLineage):
            by_content_sha256[payload.content_sha256].append(record.record_id)
            by_lineage_group_id[payload.independence_group_id].append(record.record_id)
        elif isinstance(payload, RegisteredDeduplicationDecision):
            by_lineage_group_id[payload.independence_group_id].append(record.record_id)
        elif isinstance(payload, RegisteredPolicyDecision):
            by_snapshot_fingerprint[payload.snapshot_fingerprint].append(record.record_id)
            by_source_class[payload.source_class].append(record.record_id)

    by_id_frozen = _freeze_index(by_id)
    by_snapshot_fingerprint_frozen = _freeze_index(by_snapshot_fingerprint)
    by_content_sha256_frozen = _freeze_index(by_content_sha256)
    by_provenance_fingerprint_frozen = _freeze_index(by_provenance_fingerprint)
    by_citation_id_frozen = _freeze_index(by_citation_id)
    by_lineage_group_id_frozen = _freeze_index(by_lineage_group_id)
    by_source_class_frozen = _freeze_index(by_source_class)
    by_retrieval_timestamp_frozen = _freeze_index(by_retrieval_timestamp)
    index_payload = {
        "record_ids": [record.record_id for record in ordered],
        "by_id": by_id_frozen,
        "by_snapshot_fingerprint": by_snapshot_fingerprint_frozen,
        "by_content_sha256": by_content_sha256_frozen,
        "by_provenance_fingerprint": by_provenance_fingerprint_frozen,
        "by_citation_id": by_citation_id_frozen,
        "by_lineage_group_id": by_lineage_group_id_frozen,
        "by_source_class": by_source_class_frozen,
        "by_retrieval_timestamp": by_retrieval_timestamp_frozen,
    }
    return SourceRegistryIndex(
        record_ids=tuple(record.record_id for record in ordered),
        records_by_id=by_id_frozen,
        records_by_snapshot_fingerprint=by_snapshot_fingerprint_frozen,
        records_by_content_sha256=by_content_sha256_frozen,
        records_by_provenance_fingerprint=by_provenance_fingerprint_frozen,
        records_by_citation_id=by_citation_id_frozen,
        records_by_lineage_group_id=by_lineage_group_id_frozen,
        records_by_source_class=by_source_class_frozen,
        records_by_retrieval_timestamp=by_retrieval_timestamp_frozen,
        index_fingerprint=fingerprint_payload(index_payload),
    )


def query_source_registry(
    records: tuple[SourceRegistryRecordEnvelope, ...],
    index: SourceRegistryIndex,
    query: SourceRegistryQuery,
) -> SourceRegistryQueryResult:
    """Run a bounded exact query and preserve registry order."""

    record_map = {record.record_id: record for record in records}
    if query.query_kind == "record_id":
        result_ids = index.records_by_id.get(query.value or "", ())
    elif query.query_kind == "snapshot_fingerprint":
        result_ids = index.records_by_snapshot_fingerprint.get(query.value or "", ())
    elif query.query_kind == "content_sha256":
        result_ids = index.records_by_content_sha256.get(query.value or "", ())
    elif query.query_kind == "provenance_fingerprint":
        result_ids = index.records_by_provenance_fingerprint.get(query.value or "", ())
    elif query.query_kind == "citation_id":
        result_ids = index.records_by_citation_id.get(query.value or "", ())
    elif query.query_kind == "lineage_group_id":
        result_ids = index.records_by_lineage_group_id.get(query.value or "", ())
    elif query.query_kind == "source_class":
        result_ids = index.records_by_source_class.get(query.source_class or "", ())
    else:
        result_ids = _query_retrieval_range(index, query)
    limited = result_ids[: query.limit]
    result_records = tuple(record_map[record_id] for record_id in limited)
    payload = {
        "query": query.model_dump(mode="json"),
        "record_ids": limited,
        "truncated": len(result_ids) > len(limited),
    }
    return SourceRegistryQueryResult(
        query=query,
        record_ids=tuple(limited),
        records=result_records,
        result_count=len(limited),
        truncated=len(result_ids) > len(limited),
        query_fingerprint=fingerprint_payload(payload),
    )


def _query_retrieval_range(
    index: SourceRegistryIndex,
    query: SourceRegistryQuery,
) -> tuple[str, ...]:
    start = query.retrieval_start
    end = query.retrieval_end
    if start is None or end is None:
        return ()
    collected: list[str] = []
    for timestamp, record_ids in index.records_by_retrieval_timestamp.items():
        current = datetime.fromisoformat(timestamp)
        if start <= current <= end:
            collected.extend(record_ids)
    order = {record_id: position for position, record_id in enumerate(index.record_ids)}
    return tuple(sorted(dict.fromkeys(collected), key=lambda item: order[item]))


def _freeze_index(values: dict[str, list[str]]) -> dict[str, tuple[str, ...]]:
    return {key: tuple(dict.fromkeys(values[key])) for key in sorted(values)}


__all__ = [
    "SourceRegistryIndex",
    "SourceRegistryQuery",
    "SourceRegistryQueryKind",
    "SourceRegistryQueryResult",
    "build_source_registry_index",
    "query_source_registry",
]
