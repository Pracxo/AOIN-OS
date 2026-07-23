"""Deterministic source lineage and exact deduplication."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    SOURCE_LINEAGE_SCHEMA_VERSION,
    SourceLineageKind,
    ensure_utc,
    fingerprint_payload,
    validate_hex64,
    validate_reason_codes,
    validate_safe_identifier,
)
from aion_brain.knowledge_intelligence.source_snapshot import SourceSnapshot


class SourceLineageRecord(BaseModel):
    """Lineage metadata for one snapshot without mutating or deleting it."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-lineage/v1"] = SOURCE_LINEAGE_SCHEMA_VERSION
    lineage_id: str
    snapshot_id: str
    lineage_kind: SourceLineageKind
    canonical_source_snapshot_id: str
    content_sha256: str
    canonical_url_fingerprint: str
    independence_group_id: str
    evidence: tuple[str, ...]
    created_at: datetime
    lineage_fingerprint: str

    @field_validator(
        "lineage_id",
        "snapshot_id",
        "canonical_source_snapshot_id",
        "independence_group_id",
    )
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "lineage identifier")

    @field_validator("content_sha256", "canonical_url_fingerprint", "lineage_fingerprint")
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "lineage fingerprint")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "lineage created_at")


class SourceDeduplicationDecision(BaseModel):
    """Deduplication decision preserving every snapshot as evidence."""

    model_config = FROZEN_MODEL_CONFIG

    exact_url_duplicate: bool
    canonical_url_duplicate: bool
    exact_content_duplicate: bool
    redirect_alias: bool
    suspected_mirror: bool
    independent_source_count: int = Field(ge=0)
    independence_group_id: str
    reason_codes: tuple[str, ...]
    fingerprint: str

    @field_validator("independence_group_id")
    @classmethod
    def group_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "independence_group_id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "deduplication fingerprint")


def deduplicate_source_snapshots(
    snapshots: Iterable[SourceSnapshot],
    *,
    group_id_factory: Callable[[int], str] | None = None,
) -> tuple[SourceDeduplicationDecision, ...]:
    """Group exact URL and exact-content duplicates deterministically."""

    ordered = sorted(snapshots, key=lambda item: (item.canonical_url, item.snapshot_id))
    url_counts: dict[str, int] = defaultdict(int)
    content_counts: dict[str, int] = defaultdict(int)
    for snapshot in ordered:
        url_counts[snapshot.canonical_url] += 1
        content_counts[snapshot.content_sha256] += 1
    decisions: list[SourceDeduplicationDecision] = []
    group_ids: dict[str, str] = {}
    factory = group_id_factory or (lambda index: f"research-independence-group-{index:04d}")
    for snapshot in ordered:
        content = snapshot.content_sha256
        if content not in group_ids:
            group_ids[content] = factory(len(group_ids) + 1)
        exact_url = url_counts[snapshot.canonical_url] > 1
        exact_content = content_counts[content] > 1
        redirect_alias = snapshot.final_url != snapshot.canonical_url
        suspected_mirror = exact_content and not exact_url
        reason_codes = _dedup_reason_codes(
            exact_url,
            exact_content,
            redirect_alias,
            suspected_mirror,
        )
        payload = {
            "snapshot_id": snapshot.snapshot_id,
            "exact_url": exact_url,
            "exact_content": exact_content,
            "redirect_alias": redirect_alias,
            "suspected_mirror": suspected_mirror,
            "group": group_ids[content],
            "reason_codes": reason_codes,
        }
        decisions.append(
            SourceDeduplicationDecision(
                exact_url_duplicate=exact_url,
                canonical_url_duplicate=exact_url,
                exact_content_duplicate=exact_content,
                redirect_alias=redirect_alias,
                suspected_mirror=suspected_mirror,
                independent_source_count=len(group_ids),
                independence_group_id=group_ids[content],
                reason_codes=reason_codes,
                fingerprint=fingerprint_payload(payload),
            )
        )
    return tuple(decisions)


def build_lineage_records(
    snapshots: Iterable[SourceSnapshot],
    decisions: tuple[SourceDeduplicationDecision, ...],
    *,
    created_at: datetime,
) -> tuple[SourceLineageRecord, ...]:
    """Build lineage records from deduplication decisions."""

    ordered = sorted(snapshots, key=lambda item: (item.canonical_url, item.snapshot_id))
    records: list[SourceLineageRecord] = []
    for index, (snapshot, decision) in enumerate(zip(ordered, decisions, strict=True), start=1):
        kind: SourceLineageKind = "original"
        if decision.exact_content_duplicate:
            kind = "exact_duplicate"
        elif decision.redirect_alias:
            kind = "redirect"
        payload = {
            "snapshot_id": snapshot.snapshot_id,
            "kind": kind,
            "group": decision.independence_group_id,
            "content_sha256": snapshot.content_sha256,
            "created_at": created_at.isoformat(),
        }
        records.append(
            SourceLineageRecord(
                lineage_id=f"source-lineage-{index:04d}",
                snapshot_id=snapshot.snapshot_id,
                lineage_kind=kind,
                canonical_source_snapshot_id=snapshot.snapshot_id,
                content_sha256=snapshot.content_sha256,
                canonical_url_fingerprint=decision.fingerprint,
                independence_group_id=decision.independence_group_id,
                evidence=("repetition_does_not_establish_truth",),
                created_at=created_at,
                lineage_fingerprint=fingerprint_payload(payload),
            )
        )
    return tuple(records)


def _dedup_reason_codes(
    exact_url: bool,
    exact_content: bool,
    redirect_alias: bool,
    suspected_mirror: bool,
) -> tuple[str, ...]:
    codes: list[str] = ["research_independence_not_established"]
    if exact_url:
        codes.append("research_exact_url_duplicate")
    if exact_content:
        codes.append("research_exact_content_duplicate")
    if redirect_alias:
        codes.append("research_redirect_alias")
    if suspected_mirror:
        codes.append("research_suspected_mirror")
    return tuple(codes)


__all__ = [
    "SourceDeduplicationDecision",
    "SourceLineageRecord",
    "build_lineage_records",
    "deduplicate_source_snapshots",
]
