from __future__ import annotations

from public_research_pilot_test_helpers import FIXED_TIME, PUBLIC_IPV4

from aion_brain.knowledge_intelligence.public_research_dns import (
    InMemoryPublicResearchDnsBackend,
    peer_matches_pinned_destination,
)


def test_peer_must_be_inside_pinned_set() -> None:
    destination = InMemoryPublicResearchDnsBackend(
        {"example.com": (PUBLIC_IPV4,)}, resolved_at=FIXED_TIME
    ).resolve("example.com", 443, resolution_id="resolution-0001")
    assert peer_matches_pinned_destination(PUBLIC_IPV4, destination) is True
    assert peer_matches_pinned_destination("1.1.1.1", destination) is False
