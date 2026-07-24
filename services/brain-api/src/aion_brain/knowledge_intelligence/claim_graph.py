"""Controlled immutable temporal claim-evidence graph core."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from pathlib import Path

from aion_brain.contracts.knowledge_claim_graph import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    CLAIM_GRAPH_RECORD_ENVELOPE_SCHEMA_VERSION,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ClaimEvidenceBinding,
    ClaimGraphAppendDecision,
    ClaimGraphAppendOutcome,
    ClaimGraphIntegrityStatus,
    ClaimGraphPayload,
    ClaimGraphProposedBatch,
    ClaimGraphRecordEnvelope,
    ClaimGraphRecordKind,
    ClaimGraphResourceUsage,
    ClaimPredicateCardinality,
    ClaimRelationEdge,
    ClaimRelationOrigin,
    ClaimRelationType,
    EvidenceRole,
    StructuralConflictCandidate,
    UnverifiedClaimAssertion,
    claim_graph_append_decision_fingerprint,
    claim_graph_batch_fingerprint,
    claim_graph_payload_fingerprint,
    claim_graph_record_fingerprint,
    evaluate_claim_graph_budget,
    structural_conflict_candidate_fingerprint,
)
from aion_brain.contracts.knowledge_research import fingerprint_payload, stable_json, utc_now
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredCitationReference,
    RegisteredDeduplicationDecision,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
)
from aion_brain.knowledge_intelligence.claim_graph_evidence import (
    ClaimGraphDiagnostics,
    ClaimGraphEvidenceBundle,
    ClaimGraphIncidentRecord,
    ClaimGraphOperatorReviewItem,
    claim_graph_diagnostics_payload,
    claim_graph_evidence_bundle_payload,
    claim_graph_incident_payload,
    claim_graph_operator_review_payload,
)
from aion_brain.knowledge_intelligence.claim_graph_index import (
    ClaimGraphIndex,
    ClaimGraphQuery,
    ClaimGraphQueryResult,
    build_claim_graph_index,
    query_claim_graph,
)
from aion_brain.knowledge_intelligence.claim_graph_integrity import (
    ClaimGraphIntegrityReport,
    audit_temporal_claim_evidence_graph,
)
from aion_brain.knowledge_intelligence.claim_graph_repository import (
    ExplicitLocalClaimGraphFixtureReplay,
    InMemoryTemporalClaimGraphRepository,
)
from aion_brain.knowledge_intelligence.claim_graph_temporal import claim_scopes_overlap
from aion_brain.knowledge_intelligence.source_registry_integrity import audit_source_registry


class ClaimGraphProjectionError(ValueError):
    """Raised when claim graph inputs violate the AION-208-KI-0003 boundary."""


class ControlledTemporalClaimEvidenceGraph:
    """Controlled claim-graph facade with no runtime registration or persistence."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        id_factory: Callable[[str, int], str] | None = None,
    ) -> None:
        self._clock = clock
        self._id_factory = id_factory

    def project(
        self,
        *,
        claims: Iterable[UnverifiedClaimAssertion],
        evidence_bindings: Iterable[ClaimEvidenceBinding],
        relations: Iterable[ClaimRelationEdge],
        source_registry_repository: object,
    ) -> ClaimGraphProposedBatch:
        """Project explicit unverified claims into append-only in-memory records."""

        now = self._clock()
        registry_records = _registry_records(source_registry_repository)
        registry_report = audit_source_registry(registry_records, clock=self._clock)
        if registry_report.status != "passed":
            raise ClaimGraphProjectionError("source registry integrity audit failed")
        references = _registry_reference_sets(registry_records)
        claim_values = tuple(sorted(claims, key=lambda item: item.claim_id))
        binding_values = tuple(sorted(evidence_bindings, key=lambda item: item.binding_id))
        relation_values = tuple(sorted(relations, key=lambda item: item.relation_id))
        _validate_claims(claim_values)
        _validate_evidence_bindings(binding_values, claim_values, references)
        _validate_relations(relation_values, claim_values)
        conflict_values = self.detect_structural_conflicts(claim_values)

        payloads: list[ClaimGraphPayload] = [
            *claim_values,
            *binding_values,
            *relation_values,
            *conflict_values,
        ]
        records = _make_record_chain(
            payloads,
            created_at=now,
            id_factory=self._id_factory,
        )
        usage = _usage_for_projection(
            claims=claim_values,
            evidence_bindings=binding_values,
            relations=relation_values,
            conflict_candidates=conflict_values,
            records=records,
        )
        budget_decision = evaluate_claim_graph_budget(usage)
        if not budget_decision.within_budget:
            raise ClaimGraphProjectionError("claim graph batch exceeds authorized budget")
        batch = ClaimGraphProposedBatch(
            graph_id="temporal-claim-evidence-graph",
            records=records,
            record_count=len(records),
            claim_count=len(claim_values),
            evidence_binding_count=len(binding_values),
            relation_count=len(relation_values),
            structural_conflict_candidate_count=len(conflict_values),
            budget_decision=budget_decision,
            created_at=now,
            batch_fingerprint=claim_graph_batch_fingerprint(
                {
                    "schema_version": "aion-knowledge-claim-graph-batch/v1",
                    "program_id": PROGRAM_ID,
                    "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
                    "implementation_task": IMPLEMENTATION_TASK,
                    "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
                    "authorization_scope": AUTHORIZATION_SCOPE,
                    "graph_id": "temporal-claim-evidence-graph",
                    "records": [record.model_dump(mode="json") for record in records],
                    "record_count": len(records),
                    "claim_count": len(claim_values),
                    "evidence_binding_count": len(binding_values),
                    "relation_count": len(relation_values),
                    "structural_conflict_candidate_count": len(conflict_values),
                    "budget_decision": budget_decision.model_dump(mode="json"),
                    "operator_review_required": True,
                    "persistent_write_applied": False,
                    "append_only": True,
                    "created_at": now,
                    "runtime_effect": False,
                }
            ),
        )
        return batch

    def detect_structural_conflicts(
        self,
        claims: Iterable[UnverifiedClaimAssertion],
    ) -> tuple[StructuralConflictCandidate, ...]:
        """Detect conservative structural conflict candidates without resolving them."""

        claim_values = tuple(sorted(claims, key=lambda item: item.claim_id))
        candidates: list[StructuralConflictCandidate] = []
        now = self._clock()
        for left_index, left in enumerate(claim_values):
            for right in claim_values[left_index + 1 :]:
                candidate = _structural_conflict_candidate(left, right, created_at=now)
                if candidate is not None:
                    candidates.append(candidate)
        return tuple(sorted(candidates, key=lambda item: item.candidate_id))

    def simulate_append(
        self,
        repository: InMemoryTemporalClaimGraphRepository,
        proposed_batch: ClaimGraphProposedBatch,
    ) -> tuple[InMemoryTemporalClaimGraphRepository, ClaimGraphAppendDecision]:
        """Simulate an append in memory and return a new immutable repository."""

        before = repository.record_count()
        next_repository = repository.with_simulated_append(proposed_batch)
        appended = next_repository.record_count() - before
        idempotent = proposed_batch.record_count - appended
        outcome = (
            ClaimGraphAppendOutcome.IDEMPOTENT_REPLAY
            if appended == 0 and idempotent
            else ClaimGraphAppendOutcome.SIMULATED_APPEND
        )
        reason_codes: tuple[str, ...] = ("claim_graph_record_appended_in_memory",)
        if idempotent:
            reason_codes = (
                "claim_graph_record_appended_in_memory",
                "claim_graph_idempotent_replay",
            )
        now = self._clock()
        decision = ClaimGraphAppendDecision(
            append_allowed=True,
            append_outcome=outcome,
            persistent_write_requested=False,
            appended_record_count=appended,
            idempotent_replay_count=idempotent,
            reason_codes=reason_codes,
            created_at=now,
            fingerprint=claim_graph_append_decision_fingerprint(
                _append_decision_payload(
                    append_allowed=True,
                    append_outcome=outcome,
                    persistent_write_requested=False,
                    appended_record_count=appended,
                    idempotent_replay_count=idempotent,
                    reason_codes=reason_codes,
                    created_at=now,
                )
            ),
        )
        return next_repository, decision

    def reject_persistent_write(self, record_count: int) -> ClaimGraphAppendDecision:
        """Fail closed for every persistent claim-graph write request."""

        if record_count < 0:
            raise ClaimGraphProjectionError("record_count must be non-negative")
        now = self._clock()
        reason_codes = (
            "claim_graph_persistent_write_disabled",
            "claim_graph_operator_review_required",
        )
        return ClaimGraphAppendDecision(
            append_allowed=False,
            append_outcome=ClaimGraphAppendOutcome.PERSISTENT_WRITE_DISABLED,
            persistent_write_requested=True,
            appended_record_count=0,
            reason_codes=reason_codes,
            created_at=now,
            fingerprint=claim_graph_append_decision_fingerprint(
                _append_decision_payload(
                    append_allowed=False,
                    append_outcome=ClaimGraphAppendOutcome.PERSISTENT_WRITE_DISABLED,
                    persistent_write_requested=True,
                    appended_record_count=0,
                    idempotent_replay_count=0,
                    reason_codes=reason_codes,
                    created_at=now,
                )
            ),
        )

    def replay_fixture(
        self,
        fixture_path: str | Path,
        *,
        repository_root: str | Path,
    ) -> InMemoryTemporalClaimGraphRepository:
        """Replay an explicit local synthetic fixture into memory only."""

        return ExplicitLocalClaimGraphFixtureReplay().replay(
            fixture_path,
            repository_root=repository_root,
        )

    def build_index(self, repository: InMemoryTemporalClaimGraphRepository) -> ClaimGraphIndex:
        """Build deterministic exact indexes from immutable graph records."""

        return build_claim_graph_index(repository.snapshot())

    def audit(
        self,
        repository: InMemoryTemporalClaimGraphRepository,
        *,
        source_registry_repository: object,
    ) -> ClaimGraphIntegrityReport:
        """Audit graph records against the source-registry snapshot."""

        references = _registry_reference_sets(_registry_records(source_registry_repository))
        return audit_temporal_claim_evidence_graph(
            repository.snapshot(),
            source_registry_record_ids=references.all_record_ids,
            source_snapshot_record_ids=references.snapshot_record_ids,
            source_provenance_record_ids=references.provenance_record_ids,
            citation_record_ids=references.citation_record_ids,
            lineage_record_ids=references.lineage_record_ids,
            lineage_group_ids=references.lineage_group_ids,
            clock=self._clock,
        )

    def query(
        self,
        repository: InMemoryTemporalClaimGraphRepository,
        query: ClaimGraphQuery,
    ) -> ClaimGraphQueryResult:
        """Run a bounded exact query with no truth or ranking semantics."""

        index = self.build_index(repository)
        return query_claim_graph(repository.snapshot(), index, query)

    def evidence_bundle(
        self,
        repository: InMemoryTemporalClaimGraphRepository,
        *,
        source_registry_repository: object,
        append_outcome: ClaimGraphAppendOutcome = ClaimGraphAppendOutcome.VALIDATED,
    ) -> ClaimGraphEvidenceBundle:
        """Build redacted operator-review evidence for a graph snapshot."""

        report = self.audit(repository, source_registry_repository=source_registry_repository)
        now = self._clock()
        claims = _claims_from_records(repository.snapshot())
        relations = _relations_from_records(repository.snapshot())
        diagnostics = ClaimGraphDiagnostics.model_validate(
            claim_graph_diagnostics_payload(
                diagnostic_id="claim-graph-diagnostic-0001",
                record_count=repository.record_count(),
                claim_count=repository.claim_count(),
                evidence_binding_count=repository.binding_count(),
                relation_count=repository.relation_count(),
                structural_conflict_candidate_count=(
                    repository.structural_conflict_candidate_count()
                ),
                claim_modalities=tuple(dict.fromkeys(claim.modality for claim in claims)),
                relation_types=tuple(dict.fromkeys(edge.relation_type for edge in relations)),
                jurisdiction_scope_count=sum(
                    len(claim.scope.jurisdiction_scopes) for claim in claims
                ),
                version_scope_count=sum(len(claim.scope.version_scopes) for claim in claims),
                temporal_overlap_count=sum(
                    len(claim.scope.valid_time_intervals) for claim in claims
                ),
                integrity_status=report.status,
                budget_within_limits=report.status == ClaimGraphIntegrityStatus.PASSED,
                append_outcome=append_outcome,
                chain_head_fingerprint=report.chain_head_fingerprint,
            )
        )
        incidents = (
            tuple(
                ClaimGraphIncidentRecord.model_validate(
                    claim_graph_incident_payload(
                        incident_id=f"claim-graph-incident-{index:04d}",
                        reason_codes=finding.reason_codes,
                        affected_record_ids=(
                            (finding.record_id,) if finding.record_id is not None else ()
                        ),
                        affected_claim_ids=(
                            (finding.claim_id,) if finding.claim_id is not None else ()
                        ),
                        created_at=now,
                    )
                )
                for index, finding in enumerate(report.findings, start=1)
            )
            if report.findings
            else ()
        )
        temporary_payload = {
            "bundle_id": "claim-graph-evidence-bundle-0001",
            "graph_id": "temporal-claim-evidence-graph",
            "diagnostic": diagnostics.diagnostic_fingerprint,
            "incidents": [incident.incident_fingerprint for incident in incidents],
            "created_at": now.isoformat().replace("+00:00", "Z"),
        }
        temporary_fingerprint = fingerprint_payload(temporary_payload)
        review = ClaimGraphOperatorReviewItem.model_validate(
            claim_graph_operator_review_payload(
                review_item_id="claim-graph-review-0001",
                graph_id="temporal-claim-evidence-graph",
                diagnostic_id=diagnostics.diagnostic_id,
                incident_ids=tuple(incident.incident_id for incident in incidents),
                evidence_bundle_fingerprint=temporary_fingerprint,
                created_at=now,
                expires_at=now + timedelta(days=7),
            )
        )
        return ClaimGraphEvidenceBundle.model_validate(
            claim_graph_evidence_bundle_payload(
                bundle_id="claim-graph-evidence-bundle-0001",
                graph_id="temporal-claim-evidence-graph",
                diagnostics=diagnostics,
                incidents=incidents,
                operator_review_items=(review,),
            )
        )


def _make_record_chain(
    payloads: Iterable[ClaimGraphPayload],
    *,
    created_at: datetime,
    id_factory: Callable[[str, int], str] | None,
) -> tuple[ClaimGraphRecordEnvelope, ...]:
    records: list[ClaimGraphRecordEnvelope] = []
    previous: str | None = None
    make_id = id_factory or (lambda prefix, index: f"{prefix}-{index:04d}")
    for sequence_number, payload in enumerate(payloads, start=1):
        record_kind = _payload_record_kind(payload)
        record = _make_envelope(
            record_id=make_id(f"claim-graph-{record_kind.value}", sequence_number),
            record_kind=record_kind,
            sequence_number=sequence_number,
            payload=payload,
            previous_record_fingerprint=previous,
            created_at=created_at,
        )
        records.append(record)
        previous = record.record_fingerprint
    return tuple(records)


def _make_envelope(
    *,
    record_id: str,
    record_kind: ClaimGraphRecordKind,
    sequence_number: int,
    payload: ClaimGraphPayload,
    previous_record_fingerprint: str | None,
    created_at: datetime,
) -> ClaimGraphRecordEnvelope:
    envelope_payload = {
        "schema_version": CLAIM_GRAPH_RECORD_ENVELOPE_SCHEMA_VERSION,
        "record_id": record_id,
        "record_kind": record_kind.value,
        "sequence_number": sequence_number,
        "record_version": 1,
        "supersedes_record_id": None,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "payload": payload.model_dump(mode="json"),
        "payload_fingerprint": claim_graph_payload_fingerprint(payload),
        "previous_record_fingerprint": previous_record_fingerprint,
        "created_at": created_at,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "append_only": True,
        "unverified": True,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "source_body_present": False,
        "source_body_bytes": 0,
        "runtime_effect": False,
    }
    return ClaimGraphRecordEnvelope(
        schema_version=CLAIM_GRAPH_RECORD_ENVELOPE_SCHEMA_VERSION,
        record_id=record_id,
        record_kind=record_kind,
        sequence_number=sequence_number,
        record_version=1,
        supersedes_record_id=None,
        program_id=PROGRAM_ID,
        authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
        implementation_task=IMPLEMENTATION_TASK,
        payload=payload,
        payload_fingerprint=claim_graph_payload_fingerprint(payload),
        previous_record_fingerprint=previous_record_fingerprint,
        created_at=created_at,
        record_fingerprint=claim_graph_record_fingerprint(envelope_payload),
        synthetic=True,
        read_only=True,
        redacted=True,
        append_only=True,
        unverified=True,
        truth_value_assigned=False,
        epistemic_confidence_assigned=False,
        knowledge_promoted=False,
        belief_created=False,
        belief_mutated=False,
        persistent_write_applied=False,
        source_body_present=False,
        source_body_bytes=0,
        runtime_effect=False,
    )


def _payload_record_kind(payload: ClaimGraphPayload) -> ClaimGraphRecordKind:
    if isinstance(payload, UnverifiedClaimAssertion):
        return ClaimGraphRecordKind.CLAIM_ASSERTION
    if isinstance(payload, ClaimEvidenceBinding):
        return ClaimGraphRecordKind.EVIDENCE_BINDING
    if isinstance(payload, ClaimRelationEdge):
        return ClaimGraphRecordKind.RELATION_EDGE
    return ClaimGraphRecordKind.STRUCTURAL_CONFLICT_CANDIDATE


def _validate_claims(claims: tuple[UnverifiedClaimAssertion, ...]) -> None:
    claim_ids: dict[str, str] = {}
    identity_to_object_kind: dict[str, str] = {}
    for claim in claims:
        if not claim.unverified or claim.verified:
            raise ClaimGraphProjectionError("claim must remain explicitly unverified")
        existing = claim_ids.get(claim.claim_id)
        if existing is not None and existing != claim.claim_identity_fingerprint:
            raise ClaimGraphProjectionError("same claim ID with changed identity rejected")
        claim_ids[claim.claim_id] = claim.claim_identity_fingerprint
        kind = str(claim.object_value.kind)
        existing_kind = identity_to_object_kind.get(claim.claim_identity_fingerprint)
        if existing_kind is not None and existing_kind != kind:
            raise ClaimGraphProjectionError("same identity under inconsistent object type rejected")
        identity_to_object_kind[claim.claim_identity_fingerprint] = kind


def _validate_evidence_bindings(
    bindings: tuple[ClaimEvidenceBinding, ...],
    claims: tuple[UnverifiedClaimAssertion, ...],
    references: _RegistryReferenceSets,
) -> None:
    claim_ids = {claim.claim_id for claim in claims}
    for binding in bindings:
        if binding.claim_id not in claim_ids:
            raise ClaimGraphProjectionError("claim evidence binding references missing claim")
        if set(binding.source_registry_record_ids) - references.all_record_ids:
            raise ClaimGraphProjectionError("source registry reference unresolved")
        if set(binding.source_snapshot_record_ids) - references.snapshot_record_ids:
            raise ClaimGraphProjectionError("source snapshot reference unresolved")
        if set(binding.source_provenance_record_ids) - references.provenance_record_ids:
            raise ClaimGraphProjectionError("source provenance reference unresolved")
        if set(binding.citation_record_ids) - references.citation_record_ids:
            raise ClaimGraphProjectionError("citation reference unresolved")
        if set(binding.lineage_record_ids) - references.lineage_record_ids:
            raise ClaimGraphProjectionError("source lineage reference unresolved")
        if set(binding.lineage_group_ids) - references.lineage_group_ids:
            raise ClaimGraphProjectionError("source independence group unresolved")
        if binding.evidence_role in {EvidenceRole.SUPPORTS, EvidenceRole.OPPOSES}:
            if binding.verified_support or binding.truth_effect or binding.confidence_effect:
                raise ClaimGraphProjectionError("evidence role cannot verify or rank claim")


def _validate_relations(
    relations: tuple[ClaimRelationEdge, ...],
    claims: tuple[UnverifiedClaimAssertion, ...],
) -> None:
    claim_ids = {claim.claim_id for claim in claims}
    relation_counts: Counter[str] = Counter()
    revision_edges: dict[str, set[str]] = {}
    for relation in relations:
        if relation.source_claim_id not in claim_ids or relation.target_claim_id not in claim_ids:
            raise ClaimGraphProjectionError("claim relation endpoint missing")
        relation_counts[relation.source_claim_id] += 1
        relation_counts[relation.target_claim_id] += 1
        if relation.relation_type in {
            ClaimRelationType.SUPERSEDES,
            ClaimRelationType.CORRECTS,
            ClaimRelationType.RETRACTS,
        }:
            revision_edges.setdefault(relation.source_claim_id, set()).add(relation.target_claim_id)
        if relation.relation_type == ClaimRelationType.STRUCTURAL_CONFLICT_CANDIDATE:
            if relation.relation_origin != ClaimRelationOrigin.DERIVED_STRUCTURAL:
                raise ClaimGraphProjectionError("structural conflict relation must be derived")
    if any(count > 100 for count in relation_counts.values()):
        raise ClaimGraphProjectionError("claim relation count exceeds authorized limit")
    if _has_cycle(revision_edges):
        raise ClaimGraphProjectionError("revision relation cycle rejected")


def _structural_conflict_candidate(
    left: UnverifiedClaimAssertion,
    right: UnverifiedClaimAssertion,
    *,
    created_at: datetime,
) -> StructuralConflictCandidate | None:
    if left.subject_id != right.subject_id or left.predicate != right.predicate:
        return None
    if claim_scopes_overlap(left.scope, right.scope) != "overlap":
        return None
    same_object = left.object_value.object_fingerprint == right.object_value.object_fingerprint
    polarity_conflict = same_object and left.polarity != right.polarity
    single_valued_object_conflict = (
        not same_object
        and left.predicate_cardinality == ClaimPredicateCardinality.ONE
        and right.predicate_cardinality == ClaimPredicateCardinality.ONE
    )
    mutually_exclusive_object_conflict = (
        not same_object and left.objects_mutually_exclusive and right.objects_mutually_exclusive
    )
    object_conflict = single_valued_object_conflict or mutually_exclusive_object_conflict
    if not (polarity_conflict or object_conflict):
        return None
    left_id, right_id = sorted((left.claim_id, right.claim_id))
    reason_codes = (
        "claim_graph_temporal_overlap",
        "claim_graph_jurisdiction_overlap",
        "claim_graph_version_overlap",
        "claim_graph_structural_conflict_candidate",
    )
    candidate_payload = {
        "schema_version": "aion-knowledge-structural-conflict-candidate/v1",
        "candidate_id": _candidate_id(left_id, right_id),
        "left_claim_id": left_id,
        "right_claim_id": right_id,
        "shared_subject_id": left.subject_id,
        "shared_predicate": left.predicate,
        "temporal_overlap": True,
        "jurisdiction_overlap": True,
        "version_overlap": True,
        "object_conflict": object_conflict,
        "polarity_conflict": polarity_conflict,
        "scope_sufficient": True,
        "reason_codes": reason_codes,
        "created_at": created_at,
        "structural_conflict_candidate": True,
        "contradiction_resolved": False,
        "left_claim_true": False,
        "right_claim_true": False,
        "left_claim_false": False,
        "right_claim_false": False,
        "runtime_effect": False,
    }
    return StructuralConflictCandidate(
        candidate_id=str(candidate_payload["candidate_id"]),
        left_claim_id=left_id,
        right_claim_id=right_id,
        shared_subject_id=left.subject_id,
        shared_predicate=left.predicate,
        temporal_overlap=True,
        jurisdiction_overlap=True,
        version_overlap=True,
        object_conflict=object_conflict,
        polarity_conflict=polarity_conflict,
        scope_sufficient=True,
        reason_codes=reason_codes,
        created_at=created_at,
        candidate_fingerprint=structural_conflict_candidate_fingerprint(candidate_payload),
        structural_conflict_candidate=True,
        contradiction_resolved=False,
        left_claim_true=False,
        right_claim_true=False,
        left_claim_false=False,
        right_claim_false=False,
        runtime_effect=False,
    )


def _candidate_id(left_id: str, right_id: str) -> str:
    digest = fingerprint_payload({"left": left_id, "right": right_id})[:16]
    return f"claim-graph-conflict-{digest}"


def _usage_for_projection(
    *,
    claims: tuple[UnverifiedClaimAssertion, ...],
    evidence_bindings: tuple[ClaimEvidenceBinding, ...],
    relations: tuple[ClaimRelationEdge, ...],
    conflict_candidates: tuple[StructuralConflictCandidate, ...],
    records: tuple[ClaimGraphRecordEnvelope, ...],
) -> ClaimGraphResourceUsage:
    relation_counts: Counter[str] = Counter()
    for relation in relations:
        relation_counts[relation.source_claim_id] += 1
        relation_counts[relation.target_claim_id] += 1
    for candidate in conflict_candidates:
        relation_counts[candidate.left_claim_id] += 1
        relation_counts[candidate.right_claim_id] += 1
    envelope_sizes = [
        len(stable_json(record.model_dump(mode="json")).encode("utf-8")) for record in records
    ]
    _ = envelope_sizes
    return ClaimGraphResourceUsage(
        claim_nodes=len(claims),
        evidence_bindings=len(evidence_bindings),
        claim_relation_edges=len(relations),
        maximum_source_registry_references_per_claim=max(
            (len(binding.source_registry_record_ids) for binding in evidence_bindings),
            default=0,
        ),
        maximum_citation_references_per_claim=max(
            (len(binding.citation_record_ids) for binding in evidence_bindings),
            default=0,
        ),
        maximum_lineage_groups_per_claim=max(
            (len(binding.lineage_group_ids) for binding in evidence_bindings),
            default=0,
        ),
        maximum_jurisdictions_per_claim=max(
            (len(claim.scope.jurisdiction_scopes) for claim in claims),
            default=0,
        ),
        maximum_versions_per_claim=max(
            (len(claim.scope.version_scopes) for claim in claims),
            default=0,
        ),
        maximum_temporal_intervals_per_claim=max(
            (len(claim.scope.valid_time_intervals) for claim in claims),
            default=0,
        ),
        maximum_relation_edges_per_claim=max(relation_counts.values(), default=0),
    )


class _RegistryReferenceSets:
    def __init__(
        self,
        *,
        all_record_ids: set[str],
        snapshot_record_ids: set[str],
        provenance_record_ids: set[str],
        citation_record_ids: set[str],
        lineage_record_ids: set[str],
        lineage_group_ids: set[str],
    ) -> None:
        self.all_record_ids = all_record_ids
        self.snapshot_record_ids = snapshot_record_ids
        self.provenance_record_ids = provenance_record_ids
        self.citation_record_ids = citation_record_ids
        self.lineage_record_ids = lineage_record_ids
        self.lineage_group_ids = lineage_group_ids


def _registry_records(
    source_registry_repository: object,
) -> tuple[SourceRegistryRecordEnvelope, ...]:
    snapshot = getattr(source_registry_repository, "snapshot", None)
    if not callable(snapshot):
        raise ClaimGraphProjectionError("source registry repository must provide a snapshot")
    return tuple(snapshot())


def _registry_reference_sets(
    records: tuple[SourceRegistryRecordEnvelope, ...],
) -> _RegistryReferenceSets:
    all_record_ids: set[str] = set()
    snapshot_record_ids: set[str] = set()
    provenance_record_ids: set[str] = set()
    citation_record_ids: set[str] = set()
    lineage_record_ids: set[str] = set()
    lineage_group_ids: set[str] = set()
    for record in records:
        all_record_ids.add(record.record_id)
        payload = record.payload
        if isinstance(payload, RegisteredSourceSnapshotDigest):
            snapshot_record_ids.add(record.record_id)
        elif isinstance(payload, RegisteredSourceProvenance):
            provenance_record_ids.add(record.record_id)
        elif isinstance(payload, RegisteredCitationReference):
            citation_record_ids.add(record.record_id)
        elif isinstance(payload, RegisteredSourceLineage):
            lineage_record_ids.add(record.record_id)
            lineage_group_ids.add(payload.independence_group_id)
        elif isinstance(payload, RegisteredDeduplicationDecision):
            lineage_group_ids.add(payload.independence_group_id)
    return _RegistryReferenceSets(
        all_record_ids=all_record_ids,
        snapshot_record_ids=snapshot_record_ids,
        provenance_record_ids=provenance_record_ids,
        citation_record_ids=citation_record_ids,
        lineage_record_ids=lineage_record_ids,
        lineage_group_ids=lineage_group_ids,
    )


def _claims_from_records(
    records: tuple[ClaimGraphRecordEnvelope, ...],
) -> tuple[UnverifiedClaimAssertion, ...]:
    return tuple(
        record.payload for record in records if isinstance(record.payload, UnverifiedClaimAssertion)
    )


def _relations_from_records(
    records: tuple[ClaimGraphRecordEnvelope, ...],
) -> tuple[ClaimRelationEdge, ...]:
    return tuple(
        record.payload for record in records if isinstance(record.payload, ClaimRelationEdge)
    )


def _append_decision_payload(
    *,
    append_allowed: bool,
    append_outcome: ClaimGraphAppendOutcome,
    persistent_write_requested: bool,
    appended_record_count: int,
    idempotent_replay_count: int,
    reason_codes: tuple[str, ...],
    created_at: datetime,
) -> dict[str, object]:
    return {
        "schema_version": "aion-knowledge-claim-graph-batch/v1",
        "append_allowed": append_allowed,
        "append_outcome": append_outcome.value,
        "persistent_write_requested": persistent_write_requested,
        "persistent_write_applied": False,
        "appended_record_count": appended_record_count,
        "idempotent_replay_count": idempotent_replay_count,
        "operator_review_required": True,
        "persistent_graph_write_authorization_required": True,
        "reason_codes": reason_codes,
        "created_at": created_at,
        "runtime_effect": False,
    }


def _has_cycle(edges: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for target in edges.get(node, set()):
            if visit(target):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in edges)


__all__ = [
    "ClaimGraphProjectionError",
    "ControlledTemporalClaimEvidenceGraph",
]
