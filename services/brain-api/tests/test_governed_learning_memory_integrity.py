from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_integrity_audit_passes_for_zero_effect_transaction_result():
    context = sample_transaction_context()
    report = glm.audit_promotion_transaction_result(context.result)

    assert report.status is glm.PromotionIntegrityStatus.PASSED
    assert "promotion_transaction_integrity_passed" in report.findings[0].reason_codes
    assert report.runtime_effect is False
