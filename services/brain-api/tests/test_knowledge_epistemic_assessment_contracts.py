"""AION-211 epistemic assessment contract tests."""

from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    EpistemicAssessmentStatus,
    EpistemicResourceBudget,
    EpistemicResourceUsage,
    evaluate_epistemic_budget,
    quantize_score,
)


def test_contract_exposes_evidence_posture_statuses() -> None:
    assert {status.value for status in EpistemicAssessmentStatus} == {
        "supported",
        "contradicted",
        "mixed",
        "insufficient_evidence",
        "stale",
        "superseded",
        "retracted",
        "scope_mismatch",
        "unknown",
    }


def test_resource_budget_preserves_zero_persistent_writes() -> None:
    budget = EpistemicResourceBudget()
    assert budget.maximum_persistent_assessment_write_batch == 0
    decision = evaluate_epistemic_budget(EpistemicResourceUsage())
    assert decision.within_budget is True
    assert decision.persistent_write_allowed is False
    assert quantize_score(Decimal("0.1234564")) == Decimal("0.123456")
