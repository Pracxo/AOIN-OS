from __future__ import annotations

from knowledge_source_registry_implementation_helpers import valid_batch

from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryResourceUsage,
    evaluate_source_registry_budget,
)


def test_source_registry_never_promotes_knowledge():
    batch = valid_batch()
    assert all(record.knowledge_promoted is False for record in batch.records)
    rendered = batch.model_dump_json().lower()
    assert '"knowledge_promoted":true' not in rendered
    assert '"knowledge_promotion_authorized":true' not in rendered
    decision = evaluate_source_registry_budget(
        SourceRegistryResourceUsage(knowledge_promotions=1)
    )
    assert decision.within_budget is False
    assert "source_registry_knowledge_promotion_blocked" in decision.reason_codes
