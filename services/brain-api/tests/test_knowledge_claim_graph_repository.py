from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_batch

from aion_brain.knowledge_intelligence.claim_graph_repository import (
    InMemoryTemporalClaimGraphRepository,
)


def test_repository_is_immutable_and_exposes_no_mutation_api() -> None:
    service, _registry, claims, batch = graph_batch()
    original = InMemoryTemporalClaimGraphRepository()
    updated, decision = service.simulate_append(original, batch)
    assert original.record_count() == 0
    assert updated.claim_count() == len(claims)
    assert decision.append_allowed is True
    assert updated.record_by_id(batch.records[0].record_id) == batch.records[0]
    assert updated.claim_by_id(claims[0].claim_id) == claims[0]
    for method_name in ("update", "delete", "truncate", "compact", "save"):
        assert not hasattr(updated, method_name)
