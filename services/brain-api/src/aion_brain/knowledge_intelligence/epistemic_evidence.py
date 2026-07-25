"""Redacted diagnostics, incidents, and operator-review evidence."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ClaimEpistemicAssessment,
    ConfidenceBand,
    EpistemicAssessmentBatch,
    EpistemicAssessmentEvidenceBundle,
    EpistemicAssessmentStatus,
    EpistemicDiagnostics,
    EpistemicIncidentRecord,
    EpistemicIntegrityStatus,
    EpistemicOperatorReviewItem,
    epistemic_diagnostics_fingerprint,
    epistemic_evidence_bundle_fingerprint,
    epistemic_incident_fingerprint,
    operator_review_fingerprint,
)


def incident_record(
    *,
    incident_id: str,
    reason_codes: tuple[str, ...],
    severity: str,
    created_at: datetime,
    redacted_summary: str = "Epistemic assessment boundary condition recorded.",
) -> EpistemicIncidentRecord:
    """Create one redacted incident record."""

    payload = {
        "schema_version": "aion-knowledge-epistemic-assessment-evidence/v1",
        "incident_id": incident_id,
        "reason_codes": reason_codes,
        "severity": severity,
        "redacted_summary": redacted_summary,
        "created_at": created_at,
        "runtime_effect": False,
    }
    return EpistemicIncidentRecord.model_validate(
        {**payload, "incident_fingerprint": epistemic_incident_fingerprint(payload)}
    )


def operator_review_item(
    *,
    review_item_id: str,
    assessment_ids: tuple[str, ...],
    reason_codes: tuple[str, ...],
    created_at: datetime,
) -> EpistemicOperatorReviewItem:
    """Create a bounded human-review requirement."""

    payload = {
        "schema_version": "aion-knowledge-epistemic-assessment-evidence/v1",
        "review_item_id": review_item_id,
        "assessment_ids": assessment_ids,
        "reason_codes": reason_codes,
        "created_at": created_at,
        "expires_at": created_at + timedelta(days=7),
        "operator_review_required": True,
        "human_fact_review_required": True,
        "knowledge_promotion_authorized": False,
        "belief_mutation_authorized": False,
        "persistent_assessment_write_authorized": False,
        "automatic_claim_acceptance_authorized": False,
        "automatic_claim_rejection_authorized": False,
        "approval_created": False,
        "implementation_authorization_created": False,
        "runtime_effect": False,
    }
    return EpistemicOperatorReviewItem.model_validate(
        {**payload, "review_fingerprint": operator_review_fingerprint(payload)}
    )


def diagnostics_for_batch(batch: EpistemicAssessmentBatch) -> EpistemicDiagnostics:
    """Summarise assessment statuses without claim text or source material."""

    status_counts = Counter(item.status for item in batch.assessments)
    band_counts = Counter(item.confidence_band for item in batch.assessments)
    reason_codes = tuple(
        dict.fromkeys(code for assessment in batch.assessments for code in assessment.reason_codes)
    )
    payload = {
        "schema_version": "aion-knowledge-epistemic-assessment-evidence/v1",
        "batch_id": batch.batch_id,
        "status_counts": dict(status_counts),
        "confidence_band_counts": dict(band_counts),
        "abstention_count": sum(item.explicit_abstention for item in batch.assessments),
        "integrity_status": batch.integrity_status,
        "reason_codes": reason_codes or ("epistemic_integrity_passed",),
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return EpistemicDiagnostics.model_validate(
        {
            **payload,
            "diagnostics_fingerprint": epistemic_diagnostics_fingerprint(payload),
        }
    )


def evidence_bundle_for_batch(batch: EpistemicAssessmentBatch) -> EpistemicAssessmentEvidenceBundle:
    """Create a safe operator-review evidence bundle for one batch."""

    hard_cap_ids = tuple(
        dict.fromkeys(
            cap.cap_id for assessment in batch.assessments for cap in assessment.hard_caps
        )
    )
    reason_codes = tuple(
        dict.fromkeys(code for assessment in batch.assessments for code in assessment.reason_codes)
    )
    payload = {
        "schema_version": "aion-knowledge-epistemic-assessment-evidence/v1",
        "batch_id": batch.batch_id,
        "assessment_ids": tuple(item.assessment_id for item in batch.assessments),
        "confidence_bands": tuple(item.confidence_band for item in batch.assessments),
        "statuses": tuple(item.status for item in batch.assessments),
        "hard_cap_ids": hard_cap_ids,
        "reason_codes": reason_codes or ("epistemic_integrity_passed",),
        "integrity_status": batch.integrity_status,
        "authorization_transaction_id": "AION-210-KI-0004",
        "implementation_task": "AION-211",
        "formal_closeout_task": "AION-212",
        "epistemic_truth_engine_runtime_enabled": False,
        "persistent_assessment_write_enabled": False,
        "runtime_effect": False,
    }
    return EpistemicAssessmentEvidenceBundle.model_validate(
        {
            **payload,
            "evidence_fingerprint": epistemic_evidence_bundle_fingerprint(payload),
        }
    )


def empty_diagnostics(
    *,
    batch_id: str,
    created_status: EpistemicIntegrityStatus,
) -> EpistemicDiagnostics:
    """Return deterministic empty diagnostics for rejected local fixtures."""

    payload = {
        "schema_version": "aion-knowledge-epistemic-assessment-evidence/v1",
        "batch_id": batch_id,
        "status_counts": {status: 0 for status in EpistemicAssessmentStatus},
        "confidence_band_counts": {band: 0 for band in ConfidenceBand},
        "abstention_count": 0,
        "integrity_status": created_status,
        "reason_codes": ("epistemic_integrity_failed",),
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return EpistemicDiagnostics.model_validate(
        {
            **payload,
            "diagnostics_fingerprint": epistemic_diagnostics_fingerprint(payload),
        }
    )


def assessment_ids(
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> tuple[str, ...]:
    """Return assessment IDs in existing deterministic order."""

    return tuple(item.assessment_id for item in assessments)


__all__ = [
    "assessment_ids",
    "diagnostics_for_batch",
    "empty_diagnostics",
    "evidence_bundle_for_batch",
    "incident_record",
    "operator_review_item",
]
