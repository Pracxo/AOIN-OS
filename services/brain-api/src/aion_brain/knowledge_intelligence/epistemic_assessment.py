"""Controlled deterministic epistemic evidence-assessment engine."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimEvidenceBinding,
    ClaimGraphIntegrityStatus,
    ClaimGraphRecordEnvelope,
    ClaimRelationEdge,
    StructuralConflictCandidate,
    UnverifiedClaimAssertion,
)
from aion_brain.contracts.knowledge_epistemic_assessment import (
    ClaimEpistemicAssessment,
    ConfidenceBand,
    ContradictionStatus,
    EpistemicAssessmentBatch,
    EpistemicAssessmentFixtureEnvelope,
    EpistemicAssessmentOutcome,
    EpistemicAssessmentQuery,
    EpistemicAssessmentQueryResult,
    EpistemicAssessmentRequest,
    EpistemicAssessmentStatus,
    EpistemicBudgetDecision,
    EpistemicIntegrityStatus,
    EpistemicResourceUsage,
    EpistemicScorecardPolicy,
    EpistemicTargetScope,
    EvidenceContribution,
    FreshnessStatus,
    ScopeApplicability,
    claim_epistemic_assessment_fingerprint,
    default_scorecard_policy,
    epistemic_assessment_batch_fingerprint,
    epistemic_fixture_fingerprint,
    epistemic_query_result_fingerprint,
    evaluate_epistemic_budget,
    quantize_score,
)
from aion_brain.contracts.knowledge_research import (
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    utc_now,
)
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredCitationReference,
    RegisteredDeduplicationDecision,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryRecordEnvelope,
)
from aion_brain.knowledge_intelligence.claim_graph_integrity import (
    ClaimGraphIntegrityReport,
    audit_temporal_claim_evidence_graph,
)
from aion_brain.knowledge_intelligence.claim_graph_repository import (
    InMemoryTemporalClaimGraphRepository,
    TemporalClaimGraphRepository,
)
from aion_brain.knowledge_intelligence.claim_graph_temporal import (
    valid_time_intervals_overlap,
    version_scopes_overlap,
)
from aion_brain.knowledge_intelligence.epistemic_confidence import (
    ScorecardInputs,
    build_epistemic_scorecard,
)
from aion_brain.knowledge_intelligence.epistemic_contradiction import assess_claim_relations
from aion_brain.knowledge_intelligence.epistemic_corroboration import (
    ContributionIndexes,
    build_contribution_indexes,
    counted_contributions,
    resolve_evidence_contributions,
    score_role,
)
from aion_brain.knowledge_intelligence.epistemic_evidence import operator_review_item
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    SourceRegistryIntegrityReport,
    audit_source_registry,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
    SourceRegistryRepository,
)


class EpistemicAssessmentError(ValueError):
    """Raised when AION-211 assessment input violates the authorization boundary."""


@dataclass(frozen=True)
class GraphIndexes:
    """Read-only claim-graph indexes for one assessment batch."""

    claims_by_id: dict[str, UnverifiedClaimAssertion]
    bindings_by_claim_id: dict[str, tuple[ClaimEvidenceBinding, ...]]
    relations: tuple[ClaimRelationEdge, ...]
    structural_conflicts: tuple[StructuralConflictCandidate, ...]


@dataclass(frozen=True)
class ScopeDecision:
    """Per-dimension target-scope applicability."""

    valid_time: ScopeApplicability
    valid_time_factor: Decimal
    jurisdiction: ScopeApplicability
    jurisdiction_factor: Decimal
    version: ScopeApplicability
    version_factor: Decimal

    @property
    def aggregate(self) -> ScopeApplicability:
        """Return conservative aggregate scope applicability."""

        values = (self.valid_time, self.jurisdiction, self.version)
        if ScopeApplicability.NOT_APPLICABLE in values:
            return ScopeApplicability.NOT_APPLICABLE
        if ScopeApplicability.INSUFFICIENT_SCOPE in values:
            return ScopeApplicability.INSUFFICIENT_SCOPE
        if ScopeApplicability.PARTIALLY_APPLICABLE in values:
            return ScopeApplicability.PARTIALLY_APPLICABLE
        return ScopeApplicability.APPLICABLE

    @property
    def factors(
        self,
    ) -> tuple[
        ScopeApplicability,
        Decimal,
        ScopeApplicability,
        Decimal,
        ScopeApplicability,
        Decimal,
    ]:
        """Return the contribution-factor tuple consumed by scoring helpers."""

        return (
            self.valid_time,
            self.valid_time_factor,
            self.jurisdiction,
            self.jurisdiction_factor,
            self.version,
            self.version_factor,
        )


class ControlledEpistemicAssessmentEngine:
    """Pure in-memory assessment engine with no runtime or persistence registration."""

    def __init__(self, *, clock: object = utc_now) -> None:
        self._clock = clock

    def assess(
        self,
        *,
        request: EpistemicAssessmentRequest,
        source_registry_repository: SourceRegistryRepository,
        claim_graph_repository: TemporalClaimGraphRepository,
        policy: EpistemicScorecardPolicy | None = None,
    ) -> EpistemicAssessmentBatch:
        """Assess requested unverified claims from immutable in-memory snapshots."""

        assessment_policy = policy or default_scorecard_policy()
        registry_records = tuple(source_registry_repository.snapshot())
        graph_records = tuple(claim_graph_repository.snapshot())
        registry_report = audit_source_registry(registry_records, clock=self._clock)
        graph_report = _audit_graph(graph_records, registry_records, clock=self._clock)
        graph_indexes = _build_graph_indexes(graph_records)
        contribution_indexes = build_contribution_indexes(registry_records)

        usage = _usage(request, graph_indexes, registry_records, graph_records)
        budget_decision = evaluate_epistemic_budget(usage)
        if not budget_decision.within_budget:
            raise EpistemicAssessmentError("epistemic assessment budget exceeded")

        assessments = tuple(
            self._assess_one(
                claim_id=claim_id,
                request=request,
                assessment_policy=assessment_policy,
                graph_indexes=graph_indexes,
                contribution_indexes=contribution_indexes,
                registry_report=registry_report,
                graph_report=graph_report,
            )
            for claim_id in request.claim_ids
        )
        now = self._now()
        review_reasons = tuple(
            dict.fromkeys(
                code
                for assessment in assessments
                if assessment.explicit_abstention
                for code in assessment.reason_codes
            )
        )
        reviews = (
            (
                operator_review_item(
                    review_item_id=f"epistemic-review-{request.request_id}",
                    assessment_ids=tuple(item.assessment_id for item in assessments),
                    reason_codes=review_reasons or ("epistemic_operator_review_required",),
                    created_at=now,
                ),
            )
            if review_reasons
            else ()
        )
        integrity_status = (
            EpistemicIntegrityStatus.PASSED
            if registry_report.status == "passed"
            and graph_report.status == ClaimGraphIntegrityStatus.PASSED
            else EpistemicIntegrityStatus.FAILED
        )
        outcome = (
            EpistemicAssessmentOutcome.COMPLETED_WITH_ABSTENTION
            if any(item.explicit_abstention for item in assessments)
            else EpistemicAssessmentOutcome.COMPLETED
        )
        if integrity_status == EpistemicIntegrityStatus.FAILED:
            outcome = EpistemicAssessmentOutcome.INTEGRITY_BLOCKED
        payload = {
            "schema_version": "aion-knowledge-epistemic-assessment-batch/v1",
            "batch_id": f"epistemic-batch-{request.request_id}",
            "request": request,
            "assessments": assessments,
            "assessment_count": len(assessments),
            "outcome": outcome,
            "integrity_status": integrity_status,
            "operator_review_items": reviews,
            "created_at": now,
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        return EpistemicAssessmentBatch.model_validate(
            {**payload, "batch_fingerprint": epistemic_assessment_batch_fingerprint(payload)}
        )

    def query(
        self,
        *,
        batch: EpistemicAssessmentBatch,
        query: EpistemicAssessmentQuery,
    ) -> EpistemicAssessmentQueryResult:
        """Run a bounded exact query over one in-memory batch."""

        matches = []
        for assessment in batch.assessments:
            if query.assessment_id is not None and assessment.assessment_id != query.assessment_id:
                continue
            if query.claim_id is not None and assessment.claim_id != query.claim_id:
                continue
            if query.status is not None and assessment.status != query.status:
                continue
            if (
                query.confidence_band is not None
                and assessment.confidence_band != query.confidence_band
            ):
                continue
            if (
                query.freshness_status is not None
                and assessment.freshness_status != query.freshness_status
            ):
                continue
            if (
                query.scope_applicability is not None
                and assessment.scope_applicability != query.scope_applicability
            ):
                continue
            if (
                query.contradiction_status is not None
                and assessment.contradiction_status != query.contradiction_status
            ):
                continue
            if (
                query.explicit_abstention is not None
                and assessment.explicit_abstention is not query.explicit_abstention
            ):
                continue
            matches.append(assessment)
        limited = tuple(matches[: query.limit])
        payload = {
            "schema_version": "aion-knowledge-epistemic-assessment-query/v1",
            "query": query,
            "results": limited,
            "result_count": len(limited),
            "truncated": len(matches) > len(limited),
            "runtime_effect": False,
        }
        return EpistemicAssessmentQueryResult.model_validate(
            {**payload, "query_fingerprint": epistemic_query_result_fingerprint(payload)}
        )

    def reject_persistent_write(self, record_count: int) -> EpistemicBudgetDecision:
        """Reject every persistent assessment-write request."""

        if record_count < 0:
            raise EpistemicAssessmentError("record_count must be non-negative")
        return evaluate_epistemic_budget(
            EpistemicResourceUsage(persistent_assessment_write_batch=record_count)
        )

    def replay_fixture(
        self,
        fixture_path: str | Path,
        *,
        repository_root: str | Path,
    ) -> EpistemicAssessmentBatch:
        """Replay an operator-supplied local synthetic fixture in memory only."""

        fixture = _load_fixture(fixture_path, repository_root=repository_root)
        source_records = cast(
            tuple[SourceRegistryRecordEnvelope, ...],
            fixture.source_registry_records,
        )
        graph_records = cast(tuple[ClaimGraphRecordEnvelope, ...], fixture.claim_graph_records)
        source_repository = InMemorySourceRegistryRepository(source_records)
        graph_repository = InMemoryTemporalClaimGraphRepository(graph_records)
        return self.assess(
            request=fixture.request,
            source_registry_repository=source_repository,
            claim_graph_repository=graph_repository,
        )

    def _assess_one(
        self,
        *,
        claim_id: str,
        request: EpistemicAssessmentRequest,
        assessment_policy: EpistemicScorecardPolicy,
        graph_indexes: GraphIndexes,
        contribution_indexes: ContributionIndexes,
        registry_report: SourceRegistryIntegrityReport,
        graph_report: ClaimGraphIntegrityReport,
    ) -> ClaimEpistemicAssessment:
        claim = graph_indexes.claims_by_id.get(claim_id)
        if claim is None:
            return _missing_claim_assessment(
                claim_id=claim_id,
                request=request,
                assessment_policy=assessment_policy,
                registry_report=registry_report,
                graph_report=graph_report,
            )
        scope_decision = evaluate_claim_scope_applicability(claim, request.target_scope)
        bindings = graph_indexes.bindings_by_claim_id.get(claim_id, ())
        contributions = resolve_evidence_contributions(
            bindings,
            indexes=contribution_indexes,
            claim_scope_factors=scope_decision.factors,
            freshness_policy=request.freshness_policy,
            assessment_time=request.assessment_time,
        )
        counted = counted_contributions(contributions)
        support_score = score_role(claim_id=claim_id, role="support", contributions=contributions)
        opposition_score = score_role(
            claim_id=claim_id,
            role="opposition",
            contributions=contributions,
        )
        relation_assessment = assess_claim_relations(
            claim_id=claim_id,
            relations=graph_indexes.relations,
            structural_conflicts=graph_indexes.structural_conflicts,
            independent_opposition_count=opposition_score.independent_group_count,
        )
        freshness_status = _aggregate_contribution_freshness(counted)
        scorecard = build_epistemic_scorecard(
            ScorecardInputs(
                claim_id=claim_id,
                support_score=support_score,
                opposition_score=opposition_score,
                source_registry_integrity_passed=registry_report.status == "passed",
                claim_graph_integrity_passed=(
                    graph_report.status == ClaimGraphIntegrityStatus.PASSED
                ),
                freshness_status=freshness_status,
                scope_applicability=scope_decision.aggregate,
                contradiction_status=relation_assessment.contradiction_status,
                correction_relation_count=len(relation_assessment.correction_relation_ids),
                retraction_relation_count=len(relation_assessment.retraction_relation_ids),
                supersession_relation_count=len(relation_assessment.supersession_relation_ids),
                duplicate_suppressed_count=sum(item.duplicate_suppressed for item in contributions),
                mirror_suppressed_count=sum(item.mirror_suppressed for item in contributions),
                ambiguous_group_count=sum(item.role_ambiguous for item in contributions),
                only_low_quality_evidence=_only_low_quality(counted),
                missing_citation_coverage=any(
                    item.citation_coverage_score == Decimal("0.000000") for item in counted
                ),
                incomplete_provenance=any(
                    item.provenance_completeness_score == Decimal("0.000000") for item in counted
                ),
            ),
            policy=assessment_policy,
        )
        reason_codes = tuple(
            dict.fromkeys(
                (
                    "epistemic_claim_found",
                    *relation_assessment.reason_codes,
                    *scorecard.reason_codes,
                )
            )
        )
        payload = {
            "schema_version": "aion-knowledge-claim-epistemic-assessment/v1",
            "assessment_id": f"epistemic-assessment-{claim_id}",
            "request_id": request.request_id,
            "claim_id": claim_id,
            "claim_identity_fingerprint": claim.claim_identity_fingerprint,
            "source_registry_integrity_fingerprint": registry_report.report_fingerprint,
            "claim_graph_integrity_fingerprint": graph_report.report_fingerprint,
            "assessment_policy_fingerprint": assessment_policy.policy_fingerprint,
            "scorecard_version": "aion-epistemic-scorecard/v1",
            "status": scorecard.status,
            "confidence": scorecard.confidence,
            "confidence_band": scorecard.confidence_band,
            "explicit_abstention": scorecard.explicit_abstention,
            "independent_support_count": support_score.independent_group_count,
            "independent_opposition_count": opposition_score.independent_group_count,
            "duplicate_suppressed_count": sum(item.duplicate_suppressed for item in contributions),
            "mirror_suppressed_count": sum(item.mirror_suppressed for item in contributions),
            "ambiguous_group_count": sum(item.role_ambiguous for item in contributions),
            "reference_resolution": _average_decimal(
                tuple(item.reference_resolution_score for item in counted)
            ),
            "evidence_coverage": _average_decimal(
                tuple(item.evidence_coverage_score for item in counted)
            ),
            "citation_coverage": _average_decimal(
                tuple(item.citation_coverage_score for item in counted)
            ),
            "provenance_completeness": _average_decimal(
                tuple(item.provenance_completeness_score for item in counted)
            ),
            "support_score": support_score.raw_role_score,
            "opposition_score": opposition_score.raw_role_score,
            "freshness_status": freshness_status,
            "scope_applicability": scope_decision.aggregate,
            "contradiction_status": relation_assessment.contradiction_status,
            "applicable_correction_relation_ids": relation_assessment.correction_relation_ids,
            "applicable_retraction_relation_ids": relation_assessment.retraction_relation_ids,
            "applicable_supersession_relation_ids": relation_assessment.supersession_relation_ids,
            "structural_conflict_candidate_ids": (
                relation_assessment.structural_conflict_candidate_ids
            ),
            "hard_caps": scorecard.hard_caps,
            "reason_codes": reason_codes,
            "assessment_time": request.assessment_time,
            "unverified_source_inputs": True,
            "absolute_truth_claimed": False,
            "claim_accepted": False,
            "claim_rejected": False,
            "contradiction_resolved": False,
            "knowledge_promoted": False,
            "belief_created": False,
            "belief_mutated": False,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        return ClaimEpistemicAssessment.model_validate(
            {
                **payload,
                "assessment_fingerprint": claim_epistemic_assessment_fingerprint(payload),
            }
        )

    def _now(self) -> datetime:
        now = self._clock() if callable(self._clock) else utc_now()
        if not isinstance(now, datetime):
            raise EpistemicAssessmentError("clock must return datetime")
        return now


def evaluate_valid_time_applicability(
    claim: UnverifiedClaimAssertion,
    target_scope: EpistemicTargetScope,
) -> tuple[ScopeApplicability, Decimal]:
    """Evaluate valid-time overlap against the explicit target interval."""

    overlap = valid_time_intervals_overlap(
        claim.scope.valid_time_intervals,
        (target_scope.target_valid_time,),
    )
    return _scope_result(overlap)


def evaluate_jurisdiction_applicability(
    claim: UnverifiedClaimAssertion,
    target_scope: EpistemicTargetScope,
) -> tuple[ScopeApplicability, Decimal]:
    """Evaluate jurisdiction applicability without external hierarchy lookup."""

    claim_scopes = claim.scope.jurisdiction_scopes
    if not claim_scopes or not target_scope.target_jurisdiction_ids:
        return ScopeApplicability.INSUFFICIENT_SCOPE, quantize_score("0.000000")
    target_ids = set(target_scope.target_jurisdiction_ids)
    for scope in claim_scopes:
        if scope.jurisdiction_id == "global":
            return ScopeApplicability.APPLICABLE, quantize_score("1.000000")
        if scope.jurisdiction_id in target_ids:
            return ScopeApplicability.APPLICABLE, quantize_score("1.000000")
        if target_ids.intersection(scope.parent_jurisdiction_ids):
            return ScopeApplicability.PARTIALLY_APPLICABLE, quantize_score("0.500000")
    return ScopeApplicability.NOT_APPLICABLE, quantize_score("0.000000")


def evaluate_version_applicability(
    claim: UnverifiedClaimAssertion,
    target_scope: EpistemicTargetScope,
) -> tuple[ScopeApplicability, Decimal]:
    """Evaluate explicit target version applicability."""

    overlap = version_scopes_overlap(
        claim.scope.version_scopes,
        target_scope.target_version_scopes,
    )
    return _scope_result(overlap)


def evaluate_claim_scope_applicability(
    claim: UnverifiedClaimAssertion,
    target_scope: EpistemicTargetScope,
) -> ScopeDecision:
    """Evaluate all explicit scope dimensions."""

    valid_time, valid_time_factor = evaluate_valid_time_applicability(claim, target_scope)
    jurisdiction, jurisdiction_factor = evaluate_jurisdiction_applicability(claim, target_scope)
    version, version_factor = evaluate_version_applicability(claim, target_scope)
    return ScopeDecision(
        valid_time=valid_time,
        valid_time_factor=valid_time_factor,
        jurisdiction=jurisdiction,
        jurisdiction_factor=jurisdiction_factor,
        version=version,
        version_factor=version_factor,
    )


def fixture_payload(
    *,
    request: EpistemicAssessmentRequest,
    source_registry_records: tuple[SourceRegistryRecordEnvelope, ...],
    claim_graph_records: tuple[ClaimGraphRecordEnvelope, ...],
) -> dict[str, object]:
    """Build a deterministic synthetic fixture payload."""

    payload: dict[str, object] = {
        "schema_version": "aion-knowledge-epistemic-assessment-fixture/v1",
        "program_id": "AION-KNOWLEDGE-INTELLIGENCE-001",
        "authorization_transaction_id": "AION-210-KI-0004",
        "implementation_task": "AION-211",
        "formal_closeout_task": "AION-212",
        "authorization_scope": (
            "deterministic-evidence-corroboration-contradiction-freshness-source-"
            "independence-confidence-assessment-core"
        ),
        "request": request,
        "source_registry_records": source_registry_records,
        "claim_graph_records": claim_graph_records,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return {
        **payload,
        "fixture_fingerprint": epistemic_fixture_fingerprint(payload),
    }


def _missing_claim_assessment(
    *,
    claim_id: str,
    request: EpistemicAssessmentRequest,
    assessment_policy: EpistemicScorecardPolicy,
    registry_report: SourceRegistryIntegrityReport,
    graph_report: ClaimGraphIntegrityReport,
) -> ClaimEpistemicAssessment:
    support_score = score_role(claim_id=claim_id, role="support", contributions=())
    opposition_score = score_role(claim_id=claim_id, role="opposition", contributions=())
    scorecard = build_epistemic_scorecard(
        ScorecardInputs(
            claim_id=claim_id,
            support_score=support_score,
            opposition_score=opposition_score,
            source_registry_integrity_passed=registry_report.status == "passed",
            claim_graph_integrity_passed=graph_report.status == ClaimGraphIntegrityStatus.PASSED,
            freshness_status=FreshnessStatus.UNKNOWN,
            scope_applicability=ScopeApplicability.INSUFFICIENT_SCOPE,
            contradiction_status=ContradictionStatus.NONE_DETECTED,
            correction_relation_count=0,
            retraction_relation_count=0,
            supersession_relation_count=0,
            duplicate_suppressed_count=0,
            mirror_suppressed_count=0,
            ambiguous_group_count=0,
            only_low_quality_evidence=False,
            missing_citation_coverage=True,
            incomplete_provenance=True,
        ),
        policy=assessment_policy,
    )
    reason_codes = tuple(dict.fromkeys(("epistemic_claim_missing", *scorecard.reason_codes)))
    payload = {
        "schema_version": "aion-knowledge-claim-epistemic-assessment/v1",
        "assessment_id": f"epistemic-assessment-{claim_id}",
        "request_id": request.request_id,
        "claim_id": claim_id,
        "claim_identity_fingerprint": fingerprint_payload({"missing_claim_id": claim_id}),
        "source_registry_integrity_fingerprint": registry_report.report_fingerprint,
        "claim_graph_integrity_fingerprint": graph_report.report_fingerprint,
        "assessment_policy_fingerprint": assessment_policy.policy_fingerprint,
        "scorecard_version": "aion-epistemic-scorecard/v1",
        "status": EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE,
        "confidence": Decimal("0.000000"),
        "confidence_band": ConfidenceBand.VERY_LOW,
        "explicit_abstention": True,
        "independent_support_count": 0,
        "independent_opposition_count": 0,
        "duplicate_suppressed_count": 0,
        "mirror_suppressed_count": 0,
        "ambiguous_group_count": 0,
        "reference_resolution": Decimal("0.000000"),
        "evidence_coverage": Decimal("0.000000"),
        "citation_coverage": Decimal("0.000000"),
        "provenance_completeness": Decimal("0.000000"),
        "support_score": support_score.raw_role_score,
        "opposition_score": opposition_score.raw_role_score,
        "freshness_status": FreshnessStatus.UNKNOWN,
        "scope_applicability": ScopeApplicability.INSUFFICIENT_SCOPE,
        "contradiction_status": ContradictionStatus.NONE_DETECTED,
        "applicable_correction_relation_ids": (),
        "applicable_retraction_relation_ids": (),
        "applicable_supersession_relation_ids": (),
        "structural_conflict_candidate_ids": (),
        "hard_caps": scorecard.hard_caps,
        "reason_codes": reason_codes,
        "assessment_time": request.assessment_time,
        "unverified_source_inputs": True,
        "absolute_truth_claimed": False,
        "claim_accepted": False,
        "claim_rejected": False,
        "contradiction_resolved": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ClaimEpistemicAssessment.model_validate(
        {**payload, "assessment_fingerprint": claim_epistemic_assessment_fingerprint(payload)}
    )


def _audit_graph(
    graph_records: tuple[ClaimGraphRecordEnvelope, ...],
    registry_records: tuple[SourceRegistryRecordEnvelope, ...],
    *,
    clock: object,
) -> ClaimGraphIntegrityReport:
    refs = _registry_reference_sets(registry_records)
    return audit_temporal_claim_evidence_graph(
        graph_records,
        source_registry_record_ids=refs["source_registry_record_ids"],
        source_snapshot_record_ids=refs["source_snapshot_record_ids"],
        source_provenance_record_ids=refs["source_provenance_record_ids"],
        citation_record_ids=refs["citation_record_ids"],
        lineage_record_ids=refs["lineage_record_ids"],
        lineage_group_ids=refs["lineage_group_ids"],
        clock=clock,
    )


def _registry_reference_sets(
    registry_records: tuple[SourceRegistryRecordEnvelope, ...],
) -> dict[str, tuple[str, ...]]:
    source_record_ids: list[str] = []
    snapshot_record_ids: list[str] = []
    provenance_record_ids: list[str] = []
    citation_record_ids: list[str] = []
    lineage_record_ids: list[str] = []
    lineage_group_ids: list[str] = []
    for record in registry_records:
        source_record_ids.append(record.record_id)
        payload = record.payload
        if isinstance(payload, RegisteredSourceSnapshotDigest):
            snapshot_record_ids.append(record.record_id)
        elif isinstance(payload, RegisteredSourceProvenance):
            provenance_record_ids.append(record.record_id)
        elif isinstance(payload, RegisteredCitationReference):
            citation_record_ids.append(record.record_id)
        elif isinstance(payload, RegisteredSourceLineage):
            lineage_record_ids.append(record.record_id)
            lineage_group_ids.append(payload.independence_group_id)
        elif isinstance(payload, RegisteredDeduplicationDecision):
            lineage_group_ids.append(payload.independence_group_id)
    return {
        "source_registry_record_ids": tuple(source_record_ids),
        "source_snapshot_record_ids": tuple(snapshot_record_ids),
        "source_provenance_record_ids": tuple(provenance_record_ids),
        "citation_record_ids": tuple(citation_record_ids),
        "lineage_record_ids": tuple(lineage_record_ids),
        "lineage_group_ids": tuple(sorted(set(lineage_group_ids))),
    }


def _build_graph_indexes(records: tuple[ClaimGraphRecordEnvelope, ...]) -> GraphIndexes:
    claims: dict[str, UnverifiedClaimAssertion] = {}
    bindings: defaultdict[str, list[ClaimEvidenceBinding]] = defaultdict(list)
    relations: list[ClaimRelationEdge] = []
    conflicts: list[StructuralConflictCandidate] = []
    for record in sorted(records, key=lambda item: item.sequence_number):
        payload = record.payload
        if isinstance(payload, UnverifiedClaimAssertion):
            claims[payload.claim_id] = payload
        elif isinstance(payload, ClaimEvidenceBinding):
            bindings[payload.claim_id].append(payload)
        elif isinstance(payload, ClaimRelationEdge):
            relations.append(payload)
        elif isinstance(payload, StructuralConflictCandidate):
            conflicts.append(payload)
    return GraphIndexes(
        claims_by_id=claims,
        bindings_by_claim_id={
            claim_id: tuple(sorted(values, key=lambda item: item.binding_id))
            for claim_id, values in bindings.items()
        },
        relations=tuple(sorted(relations, key=lambda item: item.relation_id)),
        structural_conflicts=tuple(sorted(conflicts, key=lambda item: item.candidate_id)),
    )


def _usage(
    request: EpistemicAssessmentRequest,
    graph_indexes: GraphIndexes,
    registry_records: tuple[SourceRegistryRecordEnvelope, ...],
    graph_records: tuple[ClaimGraphRecordEnvelope, ...],
) -> EpistemicResourceUsage:
    bindings_per_claim = max(
        (
            len(graph_indexes.bindings_by_claim_id.get(claim_id, ()))
            for claim_id in request.claim_ids
        ),
        default=0,
    )
    return EpistemicResourceUsage(
        claims_per_assessment_batch=len(request.claim_ids),
        evidence_bindings_per_claim=bindings_per_claim,
        source_registry_references_per_claim=max(
            (
                len(binding.source_registry_record_ids)
                for bindings in graph_indexes.bindings_by_claim_id.values()
                for binding in bindings
            ),
            default=0,
        ),
        citation_references_per_claim=max(
            (
                len(binding.citation_record_ids)
                for bindings in graph_indexes.bindings_by_claim_id.values()
                for binding in bindings
            ),
            default=0,
        ),
        lineage_groups_per_claim=max(
            (
                len(binding.lineage_group_ids)
                for bindings in graph_indexes.bindings_by_claim_id.values()
                for binding in bindings
            ),
            default=0,
        ),
        relation_edges_per_claim=len(graph_indexes.relations),
        reason_codes_per_assessment=50,
        operator_review_items=len(request.claim_ids),
        epistemic_assessments=len(request.claim_ids),
        confidence_calculations=len(request.claim_ids),
        fixture_records=len(registry_records) + len(graph_records),
        fixture_bytes=0,
        concurrent_assessments=1,
    )


def _scope_result(overlap: str) -> tuple[ScopeApplicability, Decimal]:
    if overlap == "overlap":
        return ScopeApplicability.APPLICABLE, quantize_score("1.000000")
    if overlap == "nonoverlap":
        return ScopeApplicability.NOT_APPLICABLE, quantize_score("0.000000")
    return ScopeApplicability.INSUFFICIENT_SCOPE, quantize_score("0.000000")


def _aggregate_contribution_freshness(
    contributions: tuple[EvidenceContribution, ...],
) -> FreshnessStatus:
    statuses = tuple(item.freshness_status for item in contributions)
    if not statuses:
        return FreshnessStatus.UNKNOWN
    if FreshnessStatus.STALE in statuses and all(
        status == FreshnessStatus.STALE for status in statuses
    ):
        return FreshnessStatus.STALE
    if FreshnessStatus.STALE in statuses or FreshnessStatus.AGEING in statuses:
        return FreshnessStatus.AGEING
    if all(status == FreshnessStatus.CURRENT for status in statuses):
        return FreshnessStatus.CURRENT
    return FreshnessStatus.UNKNOWN


def _only_low_quality(contributions: tuple[EvidenceContribution, ...]) -> bool:
    factors = tuple(item.source_quality_metadata_factor for item in contributions)
    return bool(factors) and all(factor <= Decimal("0.350000") for factor in factors)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return quantize_score("0.000000")
    return quantize_score(sum(values, Decimal("0.000000")) / Decimal(len(values)))


def _load_fixture(
    fixture_path: str | Path,
    *,
    repository_root: str | Path,
) -> EpistemicAssessmentFixtureEnvelope:
    path_text = str(fixture_path)
    if "://" in path_text or "$" in path_text or path_text.startswith("~"):
        raise EpistemicAssessmentError("fixture path must be an explicit local absolute path")
    path = Path(path_text)
    if not path.is_absolute():
        raise EpistemicAssessmentError("fixture path must be absolute")
    if any(part.startswith(".") for part in path.parts if part not in {path.anchor, "/"}):
        raise EpistemicAssessmentError("hidden fixture paths are rejected")
    root = Path(repository_root).resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        pass
    else:
        raise EpistemicAssessmentError("fixture path must be outside the repository")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise EpistemicAssessmentError("fixture file must be valid UTF-8") from exc
    reject_protected_material(text, "epistemic assessment fixture")
    data = json.loads(text)
    request = EpistemicAssessmentRequest.model_validate(data["request"])
    source_records = tuple(
        SourceRegistryRecordEnvelope.model_validate(item)
        for item in data["source_registry_records"]
    )
    graph_records = tuple(
        ClaimGraphRecordEnvelope.model_validate(item) for item in data["claim_graph_records"]
    )
    typed_payload = {
        **data,
        "request": request,
        "source_registry_records": source_records,
        "claim_graph_records": graph_records,
    }
    if data.get("fixture_fingerprint") != epistemic_fixture_fingerprint(typed_payload):
        raise EpistemicAssessmentError("epistemic fixture fingerprint mismatch")
    return EpistemicAssessmentFixtureEnvelope.model_validate(typed_payload)


def stable_assessment_json(batch: EpistemicAssessmentBatch) -> str:
    """Return deterministic JSON for tests and local evidence."""

    return stable_json(batch.model_dump(mode="json"))


__all__ = [
    "ControlledEpistemicAssessmentEngine",
    "EpistemicAssessmentError",
    "GraphIndexes",
    "ScopeDecision",
    "evaluate_claim_scope_applicability",
    "evaluate_jurisdiction_applicability",
    "evaluate_valid_time_applicability",
    "evaluate_version_applicability",
    "fixture_payload",
    "stable_assessment_json",
]
