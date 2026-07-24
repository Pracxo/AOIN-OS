from __future__ import annotations

from test_knowledge_claim_graph_helpers import LATER, NOW, graph_repository

from aion_brain.contracts.knowledge_claim_graph import ClaimRelationType
from aion_brain.knowledge_intelligence.claim_graph_index import (
    ClaimGraphQuery,
    build_claim_graph_index,
    query_claim_graph,
)


def test_queries_are_exact_bounded_and_unranked() -> None:
    repository = graph_repository()
    index = build_claim_graph_index(repository.records())
    result = query_claim_graph(
        repository.records(),
        index,
        ClaimGraphQuery(query_id="query-0001", query_kind="claim_id", value="claim-0001"),
    )
    assert result.result_count == 1
    assert result.truth_value_assigned is False
    by_relation = query_claim_graph(
        repository.records(),
        index,
        ClaimGraphQuery(
            query_id="query-0002",
            query_kind="relation_type",
            relation_type=ClaimRelationType.REFINES,
        ),
    )
    assert by_relation.result_count == 1
    by_time = query_claim_graph(
        repository.records(),
        index,
        ClaimGraphQuery(
            query_id="query-0003",
            query_kind="valid_time_range",
            valid_time_start=NOW,
            valid_time_end=LATER,
            limit=1,
        ),
    )
    assert by_time.result_count == 1
    assert by_time.truncated is True
