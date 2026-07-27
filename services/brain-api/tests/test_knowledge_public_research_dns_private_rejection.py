from __future__ import annotations

import pytest
from public_research_pilot_test_helpers import FIXED_TIME

from aion_brain.knowledge_intelligence.public_research_dns import (
    InMemoryPublicResearchDnsBackend,
    PublicResearchDnsError,
)


def test_private_loopback_linklocal_and_metadata_destinations_reject() -> None:
    for address in ("10.0.0.1", "127.0.0.1", "169.254.1.1", "169.254.169.254"):
        backend = InMemoryPublicResearchDnsBackend(
            {"example.com": (address,)}, resolved_at=FIXED_TIME
        )
        with pytest.raises(PublicResearchDnsError):
            backend.resolve("example.com", 443, resolution_id="resolution-0001")
