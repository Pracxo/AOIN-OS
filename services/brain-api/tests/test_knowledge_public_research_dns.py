from __future__ import annotations

from public_research_pilot_test_helpers import FIXED_TIME, PUBLIC_IPV4

from aion_brain.knowledge_intelligence.public_research_dns import InMemoryPublicResearchDnsBackend


def test_dns_fixture_resolves_and_pins_public_address() -> None:
    backend = InMemoryPublicResearchDnsBackend(
        {"example.com": (PUBLIC_IPV4,)}, resolved_at=FIXED_TIME
    )
    destination = backend.resolve("example.com", 443, resolution_id="resolution-0001")
    assert destination.resolution.status == "resolved_and_pinned"
    assert destination.resolution.raw_address_logged is False
