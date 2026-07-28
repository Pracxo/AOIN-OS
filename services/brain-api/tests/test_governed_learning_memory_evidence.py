from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context


def test_evidence_bundle_is_redacted_review_material_only():
    context = sample_transaction_context()
    evidence = context.result.evidence_bundle

    assert evidence.redacted is True
    assert evidence.runtime_effect is False
    assert evidence.operator_review_items[0].persistent_knowledge_write_authorized is False
    assert evidence.operator_review_items[0].runtime_effect is False
