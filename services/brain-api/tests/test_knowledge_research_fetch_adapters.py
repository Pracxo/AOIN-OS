from __future__ import annotations

import pytest
from knowledge_research_test_helpers import NOW, valid_response

from aion_brain.contracts.knowledge_research import ResearchFetchRequest, fingerprint_payload
from aion_brain.knowledge_intelligence.research_adapters import (
    DisabledResearchFetchAdapter,
    InMemoryResearchFetchAdapter,
    ResearchAdapterDisabledError,
)


def valid_request(request_id: str = "request-001") -> ResearchFetchRequest:
    payload = {"request_id": request_id, "canonical_url": "https://research.example.invalid/source.txt"}
    return ResearchFetchRequest(
        request_id=request_id,
        candidate_id="candidate-001",
        method="GET",
        canonical_url="https://research.example.invalid/source.txt",
        validated_destination={"hostname": "research.example.invalid"},
        safe_request_headers={
            "User-Agent": "AION-Knowledge-Research/disabled-operator-invoked",
            "Accept": "text/plain",
            "Accept-Language": "en",
            "Accept-Encoding": "identity",
        },
        timeout_seconds=20,
        maximum_response_bytes=1024,
        maximum_redirects=3,
        created_at=NOW,
        fingerprint=fingerprint_payload(payload),
    )


def test_disabled_fetch_adapter_fails_closed():
    with pytest.raises(ResearchAdapterDisabledError):
        DisabledResearchFetchAdapter().fetch(valid_request())


def test_in_memory_fetch_adapter_is_deterministic_and_size_bounded():
    response = valid_response(request_id="request-001")
    adapter = InMemoryResearchFetchAdapter({("GET", response.response_url): response})
    assert adapter.fetch(valid_request()).fingerprint == response.fingerprint
    with pytest.raises(ValueError):
        adapter.fetch(valid_request("request-missing"))
