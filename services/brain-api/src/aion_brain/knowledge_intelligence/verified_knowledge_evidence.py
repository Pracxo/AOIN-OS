"""Redacted verified-knowledge diagnostics, evidence, and review helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from aion_brain.contracts.knowledge_verified_memory import (
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    VERIFIED_KNOWLEDGE_EVIDENCE_SCHEMA_VERSION,
    EngagementLearningCandidate,
    EngagementSignalMetadata,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeDiagnostics,
    VerifiedKnowledgeEvidenceBundle,
    VerifiedKnowledgeIncidentRecord,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeOperatorReviewItem,
    utc_now,
    verified_knowledge_fingerprint,
)


def build_verified_knowledge_diagnostics(
    *,
    diagnostics_id: str,
    reason_codes: tuple[str, ...],
    safe_ids: tuple[str, ...] = (),
    redacted_summary: str = "verified knowledge diagnostics",
) -> VerifiedKnowledgeDiagnostics:
    """Build redacted diagnostics with safe IDs only."""

    payload = {
        "diagnostics_id": diagnostics_id,
        "reason_codes": reason_codes,
        "safe_ids": tuple(sorted(safe_ids)),
        "redacted_summary": redacted_summary,
        "redacted": True,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeDiagnostics.model_validate(
        {**payload, "diagnostics_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_verified_knowledge_incident(
    *,
    incident_id: str,
    severity_code: str,
    reason_codes: tuple[str, ...],
    candidate_ids: tuple[str, ...] = (),
    created_at: datetime | None = None,
) -> VerifiedKnowledgeIncidentRecord:
    """Build a redacted incident record without exception or content text."""

    payload = {
        "incident_id": incident_id,
        "severity_code": severity_code,
        "reason_codes": reason_codes,
        "candidate_ids": tuple(sorted(candidate_ids)),
        "created_at": created_at or utc_now(),
        "redacted": True,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeIncidentRecord.model_validate(
        {**payload, "incident_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_verified_knowledge_evidence_bundle(
    *,
    evidence_bundle_id: str,
    candidates: Iterable[VerifiedKnowledgeCandidate],
    integrity_report: VerifiedKnowledgeIntegrityReport,
    engagement_signals: Iterable[EngagementSignalMetadata] = (),
    learning_candidates: Iterable[EngagementLearningCandidate] = (),
) -> VerifiedKnowledgeEvidenceBundle:
    """Build a redacted evidence bundle from safe IDs and fingerprints only."""

    ordered_candidates = tuple(sorted(candidates, key=lambda item: item.candidate_id))
    signals = tuple(sorted(engagement_signals, key=lambda item: item.signal_id))
    learning = tuple(
        sorted(learning_candidates, key=lambda item: item.learning_candidate_id)
    )
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_EVIDENCE_SCHEMA_VERSION,
        "evidence_bundle_id": evidence_bundle_id,
        "candidate_ids": tuple(candidate.candidate_id for candidate in ordered_candidates),
        "candidate_kinds": tuple(candidate.candidate_kind for candidate in ordered_candidates),
        "eligibility_statuses": tuple(
            candidate.eligibility_decision.status for candidate in ordered_candidates
        ),
        "lifecycle_statuses": tuple(
            candidate.lifecycle_status for candidate in ordered_candidates
        ),
        "confidence_caps": tuple(
            candidate.candidate_confidence_cap for candidate in ordered_candidates
        ),
        "coverage_values": tuple(
            candidate.evidence_coverage for candidate in ordered_candidates
        ),
        "freshness_statuses": tuple(
            candidate.freshness_status for candidate in ordered_candidates
        ),
        "scope_statuses": tuple(
            candidate.scope_applicability_status for candidate in ordered_candidates
        ),
        "contradiction_statuses": tuple(
            candidate.contradiction_status for candidate in ordered_candidates
        ),
        "dissent_counts": tuple(
            len(candidate.unresolved_dissent_ids) for candidate in ordered_candidates
        ),
        "version_numbers": tuple(
            candidate.candidate_version for candidate in ordered_candidates
        ),
        "lineage_counts": tuple(
            candidate.integrated_lineage.lineage_reference_count
            for candidate in ordered_candidates
        ),
        "engagement_signal_kinds": tuple(signal.signal_kind for signal in signals),
        "learning_candidate_kinds": tuple(candidate.candidate_kind for candidate in learning),
        "integrity_status": integrity_report.status,
        "authorization_lineage": tuple(
            sorted(
                (
                    f"program-{PROGRAM_ID.lower()}",
                    f"authorization-{AUTHORIZATION_TRANSACTION_ID.lower()}",
                    f"implementation-{IMPLEMENTATION_TASK.lower()}",
                    f"closeout-{FORMAL_CLOSEOUT_TASK.lower()}",
                )
            )
        ),
        "disabled_state_flags": (
            "automatic_promotion_disabled",
            "belief_mutation_disabled",
            "cognitive_memory_write_disabled",
            "engagement_fact_effect_disabled",
            "persistent_write_disabled",
            "public_network_disabled",
            "runtime_disabled",
        ),
        "redacted": True,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeEvidenceBundle.model_validate(
        {**payload, "evidence_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_verified_knowledge_operator_review_item(
    *,
    review_item_id: str,
    candidate: VerifiedKnowledgeCandidate,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> VerifiedKnowledgeOperatorReviewItem:
    """Build an operator-review item expiring within seven days."""

    created = created_at or utc_now()
    expires = expires_at or (created + timedelta(days=7))
    if expires - created > timedelta(days=7):
        raise ValueError("operator review expiry exceeds seven days")
    payload = {
        "review_item_id": review_item_id,
        "candidate_id": candidate.candidate_id,
        "eligibility_status": candidate.eligibility_decision.status,
        "lifecycle_status": candidate.lifecycle_status,
        "reason_codes": (
            "verified_candidate_operator_review_required",
            "verified_candidate_automatic_promotion_blocked",
            "verified_candidate_cognitive_memory_write_blocked",
            "verified_candidate_belief_mutation_blocked",
            "verified_candidate_persistent_write_disabled",
        ),
        "created_at": created,
        "expires_at": expires,
        "operator_review_required": True,
        "candidate_is_not_factual_truth": True,
        "candidate_approval_authorized": False,
        "automatic_promotion_authorized": False,
        "verified_knowledge_creation_authorized": False,
        "cognitive_memory_write_authorized": False,
        "belief_mutation_authorized": False,
        "engagement_policy_update_authorized": False,
        "model_training_authorized": False,
        "persistent_write_authorized": False,
        "public_network_authorized": False,
        "approval_created": False,
        "implementation_authorization_created": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeOperatorReviewItem.model_validate(
        {**payload, "review_fingerprint": verified_knowledge_fingerprint(payload)}
    )


__all__ = [
    "build_verified_knowledge_diagnostics",
    "build_verified_knowledge_evidence_bundle",
    "build_verified_knowledge_incident",
    "build_verified_knowledge_operator_review_item",
]
