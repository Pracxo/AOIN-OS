from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_batch

from aion_brain.knowledge_intelligence.claim_graph_repository import (
    InMemoryTemporalClaimGraphRepository,
)


def test_simulated_append_is_idempotent_for_identical_replay() -> None:
    service, _registry, _claims, batch = graph_batch()
    repository, first = service.simulate_append(InMemoryTemporalClaimGraphRepository(), batch)
    replayed, second = service.simulate_append(repository, batch)
    assert first.appended_record_count == batch.record_count
    assert replayed.record_count() == repository.record_count()
    assert second.idempotent_replay_count == batch.record_count
