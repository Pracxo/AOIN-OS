from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aion_brain.knowledge_intelligence.research_policy import (
    InMemoryResearchDestinationResolver,
    validate_peer_matches_destination,
    validate_public_destination_address,
)


def test_public_ipv4_and_ipv6_are_accepted_with_synthetic_resolver():
    assert validate_public_destination_address("93.184.216.34") == "93.184.216.34"
    assert validate_public_destination_address("2606:2800:220:1:248:1893:25c8:1946")
    resolver = InMemoryResearchDestinationResolver(
        {"research.example.invalid": ("93.184.216.34",)},
        datetime(2026, 7, 23, tzinfo=UTC),
    )
    destination = resolver.resolve("research.example.invalid", 443)
    validate_peer_matches_destination("93.184.216.34", destination)
    with pytest.raises(ValueError):
        validate_peer_matches_destination("1.1.1.1", destination)


@pytest.mark.parametrize(
    "address",
    [
        "10.0.0.1",
        "127.0.0.1",
        "169.254.1.1",
        "224.0.0.1",
        "0.0.0.0",
        "169.254.169.254",
        "::1",
        "fe80::1",
        "fc00::1",
        "::ffff:10.0.0.1",
        "2130706433",
        "0177.0.0.1",
        "0x7f.0.0.1",
    ],
)
def test_destination_policy_rejects_private_local_reserved_and_encoded_bypasses(address: str):
    with pytest.raises(ValueError):
        validate_public_destination_address(address)
