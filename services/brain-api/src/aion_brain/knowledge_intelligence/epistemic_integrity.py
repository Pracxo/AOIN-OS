"""Integrity audit for in-memory epistemic assessment batches."""

from __future__ import annotations

from datetime import datetime

from pydantic import ValidationError

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ClaimEpistemicAssessment,
    EpistemicAssessmentBatch,
    EpistemicAssessmentIntegrityReport,
    EpistemicIntegrityFinding,
    EpistemicIntegrityStatus,
    epistemic_integrity_report_fingerprint,
)


def audit_epistemic_assessment_batch(
    batch: EpistemicAssessmentBatch,
    *,
    audit_timestamp: datetime,
) -> EpistemicAssessmentIntegrityReport:
    """Audit a redacted in-memory batch without mutation."""

    findings: list[EpistemicIntegrityFinding] = []
    validated = 0
    for index, assessment in enumerate(batch.assessments, start=1):
        try:
            validate_claim_assessment(assessment)
            validated += 1
        except ValueError:
            findings.append(
                _finding(
                    index,
                    reason_code="epistemic_integrity_failed",
                    assessment_id=assessment.assessment_id,
                    claim_id=assessment.claim_id,
                )
            )
    if batch.assessment_count != len(batch.assessments):
        findings.append(_finding(len(findings) + 1, reason_code="epistemic_integrity_failed"))
    status = EpistemicIntegrityStatus.PASSED if not findings else EpistemicIntegrityStatus.FAILED
    reason_codes = (
        ("epistemic_integrity_passed",)
        if status == EpistemicIntegrityStatus.PASSED
        else ("epistemic_integrity_failed",)
    )
    payload = {
        "schema_version": "aion-knowledge-epistemic-assessment-integrity/v1",
        "status": status,
        "assessment_count": batch.assessment_count,
        "validated_assessment_count": validated,
        "findings": tuple(findings),
        "reason_codes": reason_codes,
        "audit_timestamp": audit_timestamp,
        "runtime_effect": False,
    }
    return EpistemicAssessmentIntegrityReport.model_validate(
        {**payload, "report_fingerprint": epistemic_integrity_report_fingerprint(payload)}
    )


def validate_claim_assessment(assessment: ClaimEpistemicAssessment) -> ClaimEpistemicAssessment:
    """Fail closed if an assessment carries any prohibited effect."""

    try:
        rebuilt = ClaimEpistemicAssessment.model_validate(assessment.model_dump(mode="json"))
    except ValidationError as exc:
        raise ValueError("claim epistemic assessment is invalid") from exc
    if rebuilt.absolute_truth_claimed:
        raise ValueError("absolute truth claim blocked")
    if rebuilt.claim_accepted or rebuilt.claim_rejected:
        raise ValueError("automatic claim decision blocked")
    if rebuilt.contradiction_resolved:
        raise ValueError("contradiction resolution blocked")
    if rebuilt.knowledge_promoted:
        raise ValueError("knowledge promotion blocked")
    if rebuilt.belief_created or rebuilt.belief_mutated:
        raise ValueError("belief mutation blocked")
    if rebuilt.persistent_write_applied or rebuilt.runtime_effect:
        raise ValueError("runtime or persistence effect blocked")
    return rebuilt


def _finding(
    index: int,
    *,
    reason_code: str,
    assessment_id: str | None = None,
    claim_id: str | None = None,
) -> EpistemicIntegrityFinding:
    return EpistemicIntegrityFinding(
        finding_id=f"epistemic-integrity-finding-{index:04d}",
        severity="high",
        reason_codes=(reason_code,),
        assessment_id=assessment_id,
        claim_id=claim_id,
        redacted_summary="Epistemic assessment integrity invariant failed.",
    )


__all__ = [
    "audit_epistemic_assessment_batch",
    "validate_claim_assessment",
]
