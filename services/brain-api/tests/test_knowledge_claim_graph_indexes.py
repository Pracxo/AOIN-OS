from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_repository

from aion_brain.knowledge_intelligence.claim_graph_index import build_claim_graph_index


def test_indexes_are_deterministic_exact_and_tuple_backed() -> None:
    repository = graph_repository()
    first = build_claim_graph_index(repository.records())
    second = build_claim_graph_index(repository.records())
    assert first.index_fingerprint == second.index_fingerprint
    assert isinstance(next(iter(first.claims_by_claim_id.values())), tuple)
    assert first.bindings_by_source_registry_record_id[
        "source-registry-source-snapshot-digest-0001"
    ]
    assert first.structural_conflict_candidates_by_claim["claim-0001"]
