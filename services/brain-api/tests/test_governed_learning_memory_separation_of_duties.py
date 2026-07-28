from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_high_risk_belief_projection_requires_two_independent_approvers():
    one = sample_transaction_context(
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=1,
    )
    two = sample_transaction_context(
        transaction_id="promotion-transaction-two-approvers",
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
    )

    assert one.result.status is glm.PromotionTransactionStatus.BLOCKED
    assert "approval_separation_of_duties_failed" in one.result.reason_codes
    assert two.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
