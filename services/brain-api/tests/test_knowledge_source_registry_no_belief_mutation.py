from __future__ import annotations

from knowledge_source_registry_implementation_helpers import valid_batch

from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryResourceUsage,
    evaluate_source_registry_budget,
)


def test_source_registry_never_creates_or_mutates_beliefs():
    batch = valid_batch()
    rendered = batch.model_dump_json().lower()
    assert '"belief_created":true' not in rendered
    assert '"belief_mutated":true' not in rendered
    assert '"belief_mutation_authorized":true' not in rendered
    decision = evaluate_source_registry_budget(SourceRegistryResourceUsage(belief_mutations=1))
    assert decision.within_budget is False
    assert "source_registry_belief_mutation_blocked" in decision.reason_codes
