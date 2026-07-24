from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_batch

from aion_brain.knowledge_intelligence.claim_graph_repository import (
    InMemoryTemporalClaimGraphRepository,
)


def test_projection_builds_append_only_records_and_preserves_unverified_claims() -> None:
    service, registry, claims, batch = graph_batch()
    assert batch.claim_count == 2
    assert batch.structural_conflict_candidate_count == 1
    assert batch.records[0].sequence_number == 1
    assert all(record.unverified for record in batch.records)
    repository, decision = service.simulate_append(InMemoryTemporalClaimGraphRepository(), batch)
    assert repository.record_count() == batch.record_count
    assert decision.persistent_write_applied is False
    assert service.audit(repository, source_registry_repository=registry).status.value == "passed"
