from __future__ import annotations

import pytest
from knowledge_research_test_helpers import valid_candidate, valid_query

from aion_brain.knowledge_intelligence.research_adapters import (
    DisabledResearchSearchAdapter,
    InMemoryResearchSearchAdapter,
    ResearchAdapterDisabledError,
)


def test_disabled_search_adapter_fails_closed():
    with pytest.raises(ResearchAdapterDisabledError) as exc_info:
        DisabledResearchSearchAdapter().search(valid_query(), maximum_results=10)
    assert exc_info.value.reason_code == "research_search_adapter_disabled"


def test_in_memory_search_adapter_is_deterministic_and_bounded():
    query = valid_query()
    candidates = (
        valid_candidate("candidate-002", url="https://research.example.invalid/source-2.txt"),
        valid_candidate("candidate-001", url="https://research.example.invalid/source-1.txt"),
    )
    adapter = InMemoryResearchSearchAdapter({query.query_id: candidates})
    assert [item.candidate_id for item in adapter.search(query, maximum_results=1)] == [
        "candidate-001"
    ]
