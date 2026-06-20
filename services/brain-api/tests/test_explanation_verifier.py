from __future__ import annotations

from aion_brain.contracts.explanations import ExplanationRecord
from aion_brain.explanations.verifier import ExplanationVerifier


def test_verifier_warns_when_required_grounding_missing() -> None:
    record = ExplanationRecord(
        explanation_id="explanation-1",
        explanation_type="generic",
        target_type="trace",
        status="insufficient_evidence",
        title="Explanation",
        summary="AION found limited observable records.",
        confidence=0.2,
        grounded=False,
        metadata={"require_grounding": True},
    )

    verification = ExplanationVerifier().verify_explanation(record)

    assert verification.status == "warning"
    assert verification.issues[0]["code"] == "grounding_required_missing"
