from __future__ import annotations

from knowledge_source_registry_implementation_helpers import NOW, valid_batch

from aion_brain.contracts.knowledge_source_registry import (
    SourceRegistryResourceUsage,
    evaluate_source_registry_budget,
)
from aion_brain.knowledge_intelligence.source_registry import (
    reject_persistent_source_registry_write,
)
from aion_brain.knowledge_intelligence.source_registry_repository import (
    InMemorySourceRegistryRepository,
)


def test_source_registry_rejects_persistent_write_and_keeps_in_memory_records():
    batch = valid_batch()
    repository = InMemorySourceRegistryRepository().with_simulated_append(batch)
    decision = reject_persistent_source_registry_write(batch.record_count, clock=lambda: NOW)
    assert decision.append_allowed is False
    assert decision.persistent_write_applied is False
    assert repository.record_count() == batch.record_count
    budget = evaluate_source_registry_budget(SourceRegistryResourceUsage(persistent_write_batch=1))
    assert budget.within_budget is False
    assert budget.persistent_write_allowed is False
