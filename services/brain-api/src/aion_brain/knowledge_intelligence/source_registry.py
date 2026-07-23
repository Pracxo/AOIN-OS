"""Append-only source provenance registry core."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from aion_brain.contracts.knowledge_research import fingerprint_payload, stable_json, utc_now
from aion_brain.contracts.knowledge_source_registry import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    RegisteredCitationReference,
    RegisteredDeduplicationDecision,
    RegisteredOperatorReviewReference,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryAppendDecision,
    SourceRegistryPayload,
    SourceRegistryProposedBatch,
    SourceRegistryRecordEnvelope,
    SourceRegistryRecordKind,
    SourceRegistryResourceUsage,
    evaluate_source_registry_budget,
    source_registry_payload_fingerprint,
)
from aion_brain.knowledge_intelligence.research_evidence import (
    ResearchEvidenceBundle,
    ResearchOperatorReviewItem,
)
from aion_brain.knowledge_intelligence.source_deduplication import (
    SourceDeduplicationDecision,
    SourceLineageRecord,
)
from aion_brain.knowledge_intelligence.source_registry_index import (
    SourceRegistryIndex,
    SourceRegistryQuery,
    SourceRegistryQueryResult,
    build_source_registry_index,
    query_source_registry,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    SourceRegistryIntegrityReport,
    audit_source_registry,
    calculate_record_fingerprint,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    ExplicitLocalSourceRegistryFixtureReplay,
    InMemorySourceRegistryRepository,
)
from aion_brain.knowledge_intelligence.source_snapshot import SourceSnapshot


class SourceRegistryProjectionError(ValueError):
    """Raised when source evidence cannot be projected into registry metadata."""


def project_research_evidence_bundle(
    bundle: ResearchEvidenceBundle,
    *,
    clock: Callable[[], datetime] = utc_now,
    id_factory: Callable[[str, int], str] | None = None,
) -> SourceRegistryProposedBatch:
    """Project redacted AION-205 evidence into an immutable metadata-only batch."""

    _assert_bundle_safe(bundle)
    now = clock()
    make_id = id_factory or (lambda prefix, index: f"{prefix}-{index:04d}")
    proposed_count = (
        len(bundle.snapshots)
        + len(bundle.provenance_records)
        + len(bundle.citation_references)
        + len(bundle.lineage_records)
        + len(bundle.deduplication_decisions)
        + len(bundle.operator_review_items)
    )
    preflight = evaluate_source_registry_budget(
        SourceRegistryResourceUsage(registry_record_count=proposed_count)
    )
    if not preflight.within_budget:
        raise SourceRegistryProjectionError("source registry batch exceeds record budget")

    records: list[SourceRegistryRecordEnvelope] = []
    previous_fingerprint: str | None = None
    snapshot_by_id = {snapshot.snapshot_id: snapshot for snapshot in bundle.snapshots}
    provenance_by_snapshot = {
        record.snapshot_id: record for record in bundle.provenance_records
    }

    def append_payload(
        record_kind: SourceRegistryRecordKind,
        payload: SourceRegistryPayload,
    ) -> None:
        nonlocal previous_fingerprint
        sequence_number = len(records) + 1
        record = _make_envelope(
            record_id=make_id(f"source-registry-{record_kind}", sequence_number),
            record_kind=record_kind,
            sequence_number=sequence_number,
            record_version=1,
            supersedes_record_id=None,
            payload=payload,
            previous_record_fingerprint=previous_fingerprint,
            created_at=now,
        )
        records.append(record)
        previous_fingerprint = record.record_fingerprint

    for snapshot in sorted(bundle.snapshots, key=lambda item: item.snapshot_id):
        provenance = provenance_by_snapshot.get(snapshot.snapshot_id)
        canonical_url_fingerprint = (
            provenance.canonical_url_fingerprint
            if provenance is not None
            else fingerprint_payload({"canonical_url": snapshot.canonical_url})
        )
        append_payload(
            "source_snapshot_digest",
            RegisteredSourceSnapshotDigest(
                snapshot_id=snapshot.snapshot_id,
                snapshot_fingerprint=snapshot.snapshot_fingerprint,
                content_sha256=snapshot.content_sha256,
                original_url_fingerprint=snapshot.original_url_fingerprint,
                canonical_url_fingerprint=canonical_url_fingerprint,
                content_type=snapshot.content_type,
                content_length=snapshot.content_length,
                source_class=snapshot.source_class,
                robots_policy_status=snapshot.robots_policy_status,
                licence_policy_status=snapshot.licence_policy_status,
                publication_timestamp=snapshot.publication_timestamp,
                modification_timestamp=snapshot.modification_timestamp,
                retrieval_timestamp=snapshot.retrieval_timestamp,
                safe_headers_fingerprint=fingerprint_payload(snapshot.safe_headers),
                redirect_chain_fingerprint=fingerprint_payload(snapshot.redirect_chain),
            ),
        )

    for provenance in sorted(bundle.provenance_records, key=lambda item: item.provenance_id):
        snapshot = _snapshot_for(provenance.snapshot_id, snapshot_by_id)
        append_payload(
            "source_provenance",
            RegisteredSourceProvenance(
                provenance_id=provenance.provenance_id,
                provenance_fingerprint=provenance.provenance_fingerprint,
                snapshot_id=provenance.snapshot_id,
                snapshot_fingerprint=snapshot.snapshot_fingerprint,
                content_sha256=provenance.content_sha256,
                canonical_url_fingerprint=provenance.canonical_url_fingerprint,
                source_class=provenance.source_class,
                declared_author=provenance.declared_author,
                declared_publisher=provenance.declared_publisher,
                declared_title=provenance.declared_title,
                declared_publication_timestamp=provenance.declared_publication_timestamp,
                declared_modification_timestamp=provenance.declared_modification_timestamp,
                retrieval_timestamp=provenance.retrieval_timestamp,
                redirect_chain_fingerprint=provenance.redirect_chain_fingerprint,
                destination_validation_fingerprint=(
                    provenance.destination_validation_fingerprint
                ),
                safe_headers_fingerprint=provenance.safe_headers_fingerprint,
                adapter_type=provenance.adapter_type,
            ),
        )

    for citation in sorted(bundle.citation_references, key=lambda item: item.citation_id):
        snapshot = _snapshot_for(citation.snapshot_id, snapshot_by_id)
        append_payload(
            "citation_reference",
            RegisteredCitationReference(
                citation_id=citation.citation_id,
                citation_fingerprint=citation.citation_fingerprint,
                snapshot_id=citation.snapshot_id,
                snapshot_fingerprint=snapshot.snapshot_fingerprint,
                content_sha256=citation.content_sha256,
                canonical_url_fingerprint=citation.canonical_url_fingerprint,
                locator_kind=citation.locator_kind,
                locator_value=citation.locator_value,
                retrieval_timestamp=citation.retrieval_timestamp,
            ),
        )

    for lineage in sorted(bundle.lineage_records, key=lambda item: item.lineage_id):
        append_payload("source_lineage", _lineage_payload(lineage))

    snapshots_for_decisions = sorted(
        bundle.snapshots,
        key=lambda item: (item.canonical_url, item.snapshot_id),
    )
    for index, (snapshot, decision) in enumerate(
        zip(snapshots_for_decisions, bundle.deduplication_decisions, strict=True),
        start=1,
    ):
        append_payload(
            "deduplication_decision",
            _deduplication_payload(snapshot, decision, now, index),
        )

    for review in sorted(bundle.operator_review_items, key=lambda item: item.review_item_id):
        append_payload(
            "operator_review_reference",
            _operator_review_payload(review, bundle.fingerprint),
        )

    usage = _usage_for_records(tuple(records))
    budget_decision = evaluate_source_registry_budget(usage)
    if not budget_decision.within_budget:
        raise SourceRegistryProjectionError("source registry batch exceeds metadata budget")
    batch_payload = {
        "plan_id": bundle.plan_id,
        "evidence_bundle_fingerprint": bundle.fingerprint,
        "records": [record.record_fingerprint for record in records],
        "budget": budget_decision.fingerprint,
        "created_at": now.isoformat(),
    }
    return SourceRegistryProposedBatch(
        plan_id=bundle.plan_id,
        evidence_bundle_fingerprint=bundle.fingerprint,
        records=tuple(records),
        record_count=len(records),
        budget_decision=budget_decision,
        created_at=now,
        batch_fingerprint=fingerprint_payload(batch_payload),
    )


def reject_persistent_source_registry_write(
    record_count: int,
    *,
    clock: Callable[[], datetime] = utc_now,
) -> SourceRegistryAppendDecision:
    """Fail closed for every persistent-write request."""

    now = clock()
    reason_codes = (
        "source_registry_persistent_write_disabled",
        "source_registry_operator_review_required",
    )
    payload = {
        "persistent_write_requested": True,
        "record_count": record_count,
        "created_at": now.isoformat(),
        "reason_codes": reason_codes,
    }
    return SourceRegistryAppendDecision(
        append_allowed=False,
        persistent_write_requested=True,
        appended_record_count=0,
        reason_codes=reason_codes,
        created_at=now,
        fingerprint=fingerprint_payload(payload),
    )


class ControlledSourceProvenanceRegistry:
    """Controlled registry facade with no runtime registration or persistence."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str, int], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory

    def project(self, evidence_bundle: ResearchEvidenceBundle) -> SourceRegistryProposedBatch:
        """Project research evidence into a metadata-only registry batch."""

        return project_research_evidence_bundle(
            evidence_bundle,
            clock=self._clock,
            id_factory=self._id_factory,
        )

    def simulate_append(
        self,
        repository: InMemorySourceRegistryRepository,
        proposed_batch: SourceRegistryProposedBatch,
    ) -> tuple[InMemorySourceRegistryRepository, SourceRegistryAppendDecision]:
        """Simulate append in memory and return a new immutable repository."""

        before = repository.record_count()
        next_repository = repository.with_simulated_append(proposed_batch)
        appended = next_repository.record_count() - before
        idempotent = proposed_batch.record_count - appended
        now = self._clock()
        reasons: tuple[str, ...] = ("source_registry_record_appended_in_memory",)
        if idempotent:
            reasons = (
                "source_registry_record_appended_in_memory",
                "source_registry_idempotent_replay",
            )
        payload = {
            "append_allowed": True,
            "appended": appended,
            "idempotent": idempotent,
            "created_at": now.isoformat(),
            "reasons": reasons,
        }
        decision = SourceRegistryAppendDecision(
            append_allowed=True,
            persistent_write_requested=False,
            appended_record_count=appended,
            idempotent_replay_count=idempotent,
            reason_codes=reasons,
            created_at=now,
            fingerprint=fingerprint_payload(payload),
        )
        return next_repository, decision

    def replay_fixture(
        self,
        fixture_path: str | Path,
        *,
        repository_root: str | Path,
    ) -> InMemorySourceRegistryRepository:
        """Replay an explicit local synthetic fixture into memory only."""

        return ExplicitLocalSourceRegistryFixtureReplay().replay(
            fixture_path,
            repository_root=repository_root,
        )

    def build_index(self, repository: InMemorySourceRegistryRepository) -> SourceRegistryIndex:
        """Build deterministic exact indexes from a validated repository."""

        return build_source_registry_index(repository.snapshot())

    def audit(
        self,
        repository: InMemorySourceRegistryRepository,
    ) -> SourceRegistryIntegrityReport:
        """Audit a repository snapshot before returning query results."""

        return audit_source_registry(repository.snapshot(), clock=self._clock)

    def query(
        self,
        repository: InMemorySourceRegistryRepository,
        query: SourceRegistryQuery,
    ) -> SourceRegistryQueryResult:
        """Run a bounded exact query after a passing integrity audit."""

        report = self.audit(repository)
        if report.status != "passed":
            raise SourceRegistryProjectionError("source registry integrity audit failed")
        index = self.build_index(repository)
        return query_source_registry(repository.snapshot(), index, query)


def _assert_bundle_safe(bundle: ResearchEvidenceBundle) -> None:
    if not bundle.read_only or not bundle.redacted:
        raise SourceRegistryProjectionError("source registry requires read-only redacted evidence")
    if bundle.source_claims_verified or bundle.knowledge_promoted:
        raise SourceRegistryProjectionError("truth or knowledge state is not registry input")
    if bundle.belief_created or bundle.runtime_effect:
        raise SourceRegistryProjectionError("belief or runtime state is not registry input")
    for snapshot in bundle.snapshots:
        if snapshot.verified_fact or snapshot.knowledge_promoted:
            raise SourceRegistryProjectionError("snapshot truth or knowledge state blocked")
        if snapshot.belief_created or snapshot.runtime_effect:
            raise SourceRegistryProjectionError("snapshot belief or runtime state blocked")
    for provenance in bundle.provenance_records:
        if provenance.source_claims_verified:
            raise SourceRegistryProjectionError("source claim verification is blocked")
    for citation in bundle.citation_references:
        if citation.claim_verified:
            raise SourceRegistryProjectionError("verified citation claims are blocked")


def _make_envelope(
    *,
    record_id: str,
    record_kind: SourceRegistryRecordKind,
    sequence_number: int,
    record_version: int,
    supersedes_record_id: str | None,
    payload: SourceRegistryPayload,
    previous_record_fingerprint: str | None,
    created_at: datetime,
) -> SourceRegistryRecordEnvelope:
    envelope_payload = {
        "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
        "record_id": record_id,
        "record_kind": record_kind,
        "sequence_number": sequence_number,
        "record_version": record_version,
        "supersedes_record_id": supersedes_record_id,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "payload": payload,
        "payload_fingerprint": source_registry_payload_fingerprint(payload),
        "previous_record_fingerprint": previous_record_fingerprint,
        "created_at": created_at,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "append_only": True,
        "source_body_present": False,
        "source_body_bytes": 0,
        "claim_verified": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    record_fingerprint = calculate_record_fingerprint(envelope_payload)
    return SourceRegistryRecordEnvelope(
        schema_version="aion-knowledge-source-registry-record-envelope/v1",
        record_id=record_id,
        record_kind=record_kind,
        sequence_number=sequence_number,
        record_version=record_version,
        supersedes_record_id=supersedes_record_id,
        program_id=PROGRAM_ID,
        authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
        implementation_task=IMPLEMENTATION_TASK,
        formal_closeout_task=FORMAL_CLOSEOUT_TASK,
        authorization_scope=AUTHORIZATION_SCOPE,
        payload=payload,
        payload_fingerprint=source_registry_payload_fingerprint(payload),
        previous_record_fingerprint=previous_record_fingerprint,
        created_at=created_at,
        record_fingerprint=record_fingerprint,
        synthetic=True,
        read_only=True,
        redacted=True,
        append_only=True,
        source_body_present=False,
        source_body_bytes=0,
        claim_verified=False,
        knowledge_promoted=False,
        belief_created=False,
        belief_mutated=False,
        persistent_write_applied=False,
        runtime_effect=False,
    )


def _snapshot_for(
    snapshot_id: str,
    snapshot_by_id: dict[str, SourceSnapshot],
) -> SourceSnapshot:
    try:
        return snapshot_by_id[snapshot_id]
    except KeyError as exc:
        raise SourceRegistryProjectionError("source registry snapshot reference missing") from exc


def _lineage_payload(lineage: SourceLineageRecord) -> RegisteredSourceLineage:
    return RegisteredSourceLineage(
        lineage_id=lineage.lineage_id,
        lineage_fingerprint=lineage.lineage_fingerprint,
        snapshot_id=lineage.snapshot_id,
        canonical_source_snapshot_id=lineage.canonical_source_snapshot_id,
        lineage_kind=lineage.lineage_kind,
        content_sha256=lineage.content_sha256,
        canonical_url_fingerprint=lineage.canonical_url_fingerprint,
        independence_group_id=lineage.independence_group_id,
        created_at=lineage.created_at,
    )


def _deduplication_payload(
    snapshot: SourceSnapshot,
    decision: SourceDeduplicationDecision,
    created_at: datetime,
    index: int,
) -> RegisteredDeduplicationDecision:
    payload = {
        "snapshot_id": snapshot.snapshot_id,
        "decision": decision.fingerprint,
        "group": decision.independence_group_id,
        "created_at": created_at.isoformat(),
    }
    return RegisteredDeduplicationDecision(
        decision_id=f"source-registry-deduplication-{index:04d}",
        decision_fingerprint=fingerprint_payload(payload),
        snapshot_id=snapshot.snapshot_id,
        exact_url_duplicate=decision.exact_url_duplicate,
        canonical_url_duplicate=decision.canonical_url_duplicate,
        exact_content_duplicate=decision.exact_content_duplicate,
        redirect_alias=decision.redirect_alias,
        suspected_mirror=decision.suspected_mirror,
        independence_group_id=decision.independence_group_id,
        independent_source_count=decision.independent_source_count,
        reason_codes=_registry_dedup_reason_codes(decision),
        created_at=created_at,
    )


def _operator_review_payload(
    review: ResearchOperatorReviewItem,
    evidence_bundle_fingerprint: str,
) -> RegisteredOperatorReviewReference:
    return RegisteredOperatorReviewReference(
        review_item_id=review.review_item_id,
        plan_id=review.plan_id,
        source_snapshot_ids=review.snapshot_ids,
        evidence_bundle_fingerprint=evidence_bundle_fingerprint,
        created_at=review.created_at,
        expires_at=review.expires_at,
    )


def _registry_dedup_reason_codes(
    decision: SourceDeduplicationDecision,
) -> tuple[str, ...]:
    codes: list[str] = ["source_registry_record_valid"]
    if decision.exact_url_duplicate:
        codes.append("source_registry_idempotent_replay")
    if decision.exact_content_duplicate:
        codes.append("source_registry_idempotent_replay")
    return tuple(dict.fromkeys(codes))


def _usage_for_records(
    records: tuple[SourceRegistryRecordEnvelope, ...],
) -> SourceRegistryResourceUsage:
    envelope_sizes = [
        len(stable_json(record.model_dump(mode="json")).encode("utf-8")) for record in records
    ]
    payload_sizes = [
        len(stable_json(record.payload.model_dump(mode="json")).encode("utf-8"))
        for record in records
    ]
    return SourceRegistryResourceUsage(
        registry_record_count=len(records),
        largest_record_envelope_bytes=max(envelope_sizes, default=0),
        largest_metadata_bytes_per_record=max(payload_sizes, default=0),
        maximum_lineage_references_per_record=1
        if any(record.record_kind == "source_lineage" for record in records)
        else 0,
        maximum_citation_references_per_record=1
        if any(record.record_kind == "citation_reference" for record in records)
        else 0,
    )


__all__ = [
    "ControlledSourceProvenanceRegistry",
    "SourceRegistryProjectionError",
    "project_research_evidence_bundle",
    "reject_persistent_source_registry_write",
]
