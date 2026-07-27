from __future__ import annotations

import pytest
from public_research_pilot_test_helpers import FIXED_TIME, PUBLIC_IPV4

from aion_brain.knowledge_intelligence.public_research_dns import (
    InMemoryPublicResearchDnsBackend,
    PublicResearchDnsError,
    peer_fingerprint,
)


def test_peer_fingerprint_requires_pinned_peer() -> None:
    destination = InMemoryPublicResearchDnsBackend(
        {"example.com": (PUBLIC_IPV4,)}, resolved_at=FIXED_TIME
    ).resolve("example.com", 443, resolution_id="resolution-0001")
    assert peer_fingerprint(PUBLIC_IPV4, destination)
    with pytest.raises(PublicResearchDnsError):
        peer_fingerprint("1.1.1.1", destination)
