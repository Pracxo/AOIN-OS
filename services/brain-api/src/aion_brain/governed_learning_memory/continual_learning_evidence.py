"""Redacted evidence and operator review for AION-228."""

from __future__ import annotations

from aion_brain.contracts.governed_continual_learning import (
    AUTHORIZATION_TRANSACTION_ID,
    ContinualLearningDiagnostics,
    ContinualLearningEvidenceBundle,
    ContinualLearningIntegrityReport,
    ContinualLearningOperatorReviewItem,
    ContinualLearningSessionResult,
    build_record,
    utc_now,
)


def build_operator_review_item(
    *,
    session_id: str,
    review_item_id: str = "aion-228-operator-review",
    cycle_id: str | None = None,
    reason_codes: tuple[str, ...] = ("operator_review_required",),
    redacted_summary: str = "Controlled local continual-learning pilot evidence requires review.",
) -> ContinualLearningOperatorReviewItem:
    """Build a redacted operator-review item with every production boundary explicit."""

    return build_record(
        ContinualLearningOperatorReviewItem,
        {
            "review_item_id": review_item_id,
            "session_id": session_id,
            "cycle_id": cycle_id,
            "reason_codes": reason_codes,
            "redacted_summary": redacted_summary,
            "created_at": utc_now(),
        },
        "review_item_fingerprint",
    )


def build_evidence_bundle(
    *,
    session_result: ContinualLearningSessionResult,
    integrity_report: ContinualLearningIntegrityReport,
    review_items: tuple[ContinualLearningOperatorReviewItem, ...],
) -> ContinualLearningEvidenceBundle:
    """Build committed redacted evidence for the completed pilot."""

    diagnostics = (
        ContinualLearningDiagnostics(
            diagnostics_id="aion-228-diagnostics",
            reason_codes=("redacted_evidence_only", "temporary_state_removed"),
            redacted_summary="Evidence contains fingerprints, counts and outcomes only.",
            created_at=utc_now(),
        ),
    )
    return build_record(
        ContinualLearningEvidenceBundle,
        {
            "schema_version": "aion-glm-continual-learning-evidence/v1",
            "evidence_bundle_id": "aion-228-controlled-local-continual-learning-evidence",
            "session_id": session_result.session_id,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "session_result_fingerprint": session_result.result_fingerprint,
            "integrity_report_fingerprint": integrity_report.integrity_report_fingerprint,
            "operator_review_item_fingerprints": tuple(
                item.review_item_fingerprint for item in review_items
            ),
            "diagnostics": diagnostics,
            "created_at": utc_now(),
        },
        "evidence_bundle_fingerprint",
    )
