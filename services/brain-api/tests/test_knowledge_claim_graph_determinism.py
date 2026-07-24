from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_batch, graph_repository

from aion_brain.knowledge_intelligence.claim_graph_index import build_claim_graph_index


def test_fixed_inputs_produce_identical_graph_index_and_state() -> None:
    first = graph_batch()[3]
    second = graph_batch()[3]
    assert [record.record_fingerprint for record in first.records] == [
        record.record_fingerprint for record in second.records
    ]
    repository = graph_repository()
    assert (
        build_claim_graph_index(repository.records()).index_fingerprint
        == build_claim_graph_index(repository.records()).index_fingerprint
    )
    assert repository.state().state_fingerprint == repository.state().state_fingerprint
