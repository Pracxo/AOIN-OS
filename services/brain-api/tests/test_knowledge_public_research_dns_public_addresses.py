from __future__ import annotations

import ipaddress

from aion_brain.knowledge_intelligence.public_research_dns import classify_public_address


def test_public_ipv4_and_ipv6_are_accepted() -> None:
    assert classify_public_address(ipaddress.ip_address("1.1.1.1")) == "resolved_and_pinned"
    assert (
        classify_public_address(ipaddress.ip_address("2606:4700:4700::1111"))
        == "resolved_and_pinned"
    )
