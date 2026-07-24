from __future__ import annotations

import time

from test_knowledge_claim_graph_helpers import (
    claim,
    evidence_binding,
    graph_batch,
    graph_repository,
    scope,
    text_object,
)

from aion_brain.knowledge_intelligence.claim_graph_index import (
    ClaimGraphQuery,
    build_claim_graph_index,
    query_claim_graph,
)


def test_ci_safe_claim_graph_performance_smoke(tmp_path) -> None:
    start = time.monotonic()
    for index in range(10_000):
        claim(f"claim-perf-{index:04d}", object_value=text_object("alpha"))
    for index in range(10_000):
        fingerprint = claim(f"claim-identity-{index:04d}").claim_identity_fingerprint
        assert fingerprint
    first_scope = scope()
    second_scope = scope()
    from aion_brain.knowledge_intelligence.claim_graph_temporal import claim_scopes_overlap

    for _index in range(5_000):
        assert claim_scopes_overlap(first_scope, second_scope) == "overlap"
    for _index in range(2_000):
        evidence_binding()
    for _index in range(2_000):
        payload = graph_batch()[3].records[2].payload
        assert payload is not None
    service, registry, claims, batch = graph_batch()
    for _index in range(1_000):
        service.detect_structural_conflicts(claims)
    for _index in range(1_000):
        record_count = graph_batch()[3].record_count
        assert record_count
    repository = graph_repository()
    empty_repo = __import__(
        "aion_brain.knowledge_intelligence.claim_graph_repository",
        fromlist=["InMemoryTemporalClaimGraphRepository"],
    ).InMemoryTemporalClaimGraphRepository()
    for _index in range(1_000):
        service.simulate_append(empty_repo, batch)
    for _index in range(1_000):
        build_claim_graph_index(repository.records())
    for _index in range(1_000):
        service.audit(repository, source_registry_repository=registry)
    index = build_claim_graph_index(repository.records())
    query = ClaimGraphQuery(query_id="query-0001", query_kind="claim_id", value="claim-0001")
    for _index in range(5_000):
        query_claim_graph(repository.records(), index, query)
    assert time.monotonic() - start < 60
