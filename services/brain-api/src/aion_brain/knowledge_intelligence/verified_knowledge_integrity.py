"""Integrity audits for verified-knowledge candidate memory."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ValidationError

from aion_brain.contracts.knowledge_verified_memory import (
    VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
    IntegratedKnowledgeLineage,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateHistory,
    VerifiedKnowledgeCandidateMemorySnapshot,
    VerifiedKnowledgeCandidateVersion,
    VerifiedKnowledgeEligibilityStatus,
    VerifiedKnowledgeIntegrityFinding,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeIntegrityStatus,
    VerifiedKnowledgeLifecycleStatus,
    verified_knowledge_fingerprint,
)
from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
    audit_engagement_learning_candidates,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    audit_engagement_signal_batch,
)


class _AuditableRepository(Protocol):
    def snapshot(self, snapshot_id: str = "verified-memory-snapshot-001") -> (
        VerifiedKnowledgeCandidateMemorySnapshot
    ): ...


def _model_audit(
    *,
    report_id: str,
    finding_id: str,
    model: BaseModel,
    safe_ids: tuple[str, ...],
    fingerprints: tuple[str, ...],
    passed_reason: str,
    failed_reason: str = "verified_memory_integrity_failed",
    extra_pass: bool = True,
) -> VerifiedKnowledgeIntegrityReport:
    status = VerifiedKnowledgeIntegrityStatus.PASSED
    reason = passed_reason
    try:
        type(model).model_validate(model.model_dump(mode="python"))
    except ValidationError:
        status = VerifiedKnowledgeIntegrityStatus.FAILED
        reason = failed_reason
    if not extra_pass:
        status = VerifiedKnowledgeIntegrityStatus.FAILED
        reason = failed_reason
    finding = VerifiedKnowledgeIntegrityFinding.model_validate(
        {
            "finding_id": finding_id,
            "status": status,
            "reason_codes": (reason,),
            "safe_ids": tuple(sorted(safe_ids)),
            "fingerprints": tuple(sorted(fingerprints)),
            "bounded_count": len(safe_ids) + len(fingerprints),
            "redacted_summary": "verified knowledge integrity audit",
            "runtime_effect": False,
        }
    )
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
        "report_id": report_id,
        "status": status,
        "findings": (finding,),
        "finding_count": 1,
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeIntegrityReport.model_validate(
        {**payload, "report_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def audit_verified_knowledge_candidate(
    candidate: VerifiedKnowledgeCandidate,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit candidate confidence, lineage, and disabled-effect fields."""

    extra_pass = (
        candidate.candidate_confidence_cap <= candidate.assessment_confidence
        and candidate.operator_review_required
        and not candidate.automatic_promotion
        and not candidate.persistent_write_applied
        and not candidate.cognitive_memory_written
        and not candidate.belief_mutated
        and not candidate.runtime_effect
    )
    return _model_audit(
        report_id=f"integrity-{candidate.candidate_id}",
        finding_id=f"finding-{candidate.candidate_id}",
        model=candidate,
        safe_ids=(candidate.candidate_id, candidate.candidate_identity_id),
        fingerprints=(
            candidate.candidate_fingerprint,
            candidate.integrated_lineage.lineage_fingerprint,
        ),
        passed_reason="verified_candidate_integrity_passed",
        failed_reason="verified_candidate_integrity_failed",
        extra_pass=extra_pass,
    )


def audit_verified_knowledge_candidate_version(
    version: VerifiedKnowledgeCandidateVersion,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit one immutable candidate version."""

    extra_pass = (
        version.candidate.candidate_version == version.version_number
        and not version.persistent_write_applied
        and not version.cognitive_memory_written
        and not version.belief_mutated
        and not version.runtime_effect
    )
    return _model_audit(
        report_id=f"integrity-{version.candidate_version_id}",
        finding_id=f"finding-{version.candidate_version_id}",
        model=version,
        safe_ids=(version.candidate_version_id, version.candidate_id),
        fingerprints=(version.version_fingerprint, version.candidate.candidate_fingerprint),
        passed_reason="verified_candidate_version_created",
        failed_reason="verified_candidate_integrity_failed",
        extra_pass=extra_pass,
    )


def audit_verified_knowledge_candidate_history(
    history: VerifiedKnowledgeCandidateHistory,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit contiguous candidate history preservation."""

    extra_pass = (
        history.version_count == len(history.versions)
        and tuple(version.version_number for version in history.versions)
        == tuple(range(1, len(history.versions) + 1))
        and not history.persistent_write_applied
        and not history.runtime_effect
    )
    return _model_audit(
        report_id=f"integrity-{history.candidate_identity_id}",
        finding_id=f"finding-{history.candidate_identity_id}",
        model=history,
        safe_ids=(history.candidate_identity_id, history.latest_candidate_version_id),
        fingerprints=(history.history_fingerprint,),
        passed_reason="verified_candidate_history_preserved",
        failed_reason="verified_candidate_integrity_failed",
        extra_pass=extra_pass,
    )


def audit_verified_knowledge_memory_snapshot(
    snapshot: VerifiedKnowledgeCandidateMemorySnapshot,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit one deterministic memory snapshot."""

    return _model_audit(
        report_id=f"integrity-{snapshot.snapshot_id}",
        finding_id=f"finding-{snapshot.snapshot_id}",
        model=snapshot,
        safe_ids=(snapshot.snapshot_id, *snapshot.candidate_ids),
        fingerprints=(snapshot.snapshot_fingerprint,),
        passed_reason="verified_memory_integrity_passed",
        failed_reason="verified_memory_integrity_failed",
        extra_pass=not snapshot.persistent_write_applied and not snapshot.runtime_effect,
    )


def audit_verified_knowledge_repository(
    repository: _AuditableRepository,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit repository snapshot integrity without persisting state."""

    snapshot = repository.snapshot("verified-memory-repository-audit")
    return audit_verified_knowledge_memory_snapshot(snapshot)


def audit_integrated_knowledge_lineage(
    lineage: IntegratedKnowledgeLineage,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit lineage model integrity."""

    return _model_audit(
        report_id=f"integrity-{lineage.lineage_id}",
        finding_id=f"finding-{lineage.lineage_id}",
        model=lineage,
        safe_ids=(lineage.lineage_id, lineage.claim_id),
        fingerprints=(lineage.lineage_fingerprint,),
        passed_reason="verified_lineage_valid",
        failed_reason="verified_lineage_invalid",
        extra_pass=not lineage.runtime_effect,
    )


def audit_candidate_policy_status(
    candidate: VerifiedKnowledgeCandidate,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit lifecycle and eligibility policy binding."""

    expected_review = (
        candidate.eligibility_decision.status
        is VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    )
    actual_review = (
        candidate.lifecycle_status is VerifiedKnowledgeLifecycleStatus.OPERATOR_REVIEW_PENDING
    )
    return _model_audit(
        report_id=f"integrity-policy-{candidate.candidate_id}",
        finding_id=f"finding-policy-{candidate.candidate_id}",
        model=candidate,
        safe_ids=(candidate.candidate_id,),
        fingerprints=(candidate.candidate_fingerprint,),
        passed_reason="verified_candidate_integrity_passed",
        failed_reason="verified_candidate_integrity_failed",
        extra_pass=expected_review == actual_review,
    )


__all__ = [
    "audit_candidate_policy_status",
    "audit_engagement_learning_candidates",
    "audit_engagement_signal_batch",
    "audit_integrated_knowledge_lineage",
    "audit_verified_knowledge_candidate",
    "audit_verified_knowledge_candidate_history",
    "audit_verified_knowledge_candidate_version",
    "audit_verified_knowledge_memory_snapshot",
    "audit_verified_knowledge_repository",
]
