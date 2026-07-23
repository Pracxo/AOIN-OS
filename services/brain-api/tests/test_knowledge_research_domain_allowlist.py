from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.research_policy import (
    host_is_allowlisted,
    validate_domain_allowlist,
)


def test_exact_and_wildcard_hosts_are_label_boundary_checked():
    policy = validate_domain_allowlist(
        ("research.example.invalid",),
        ("*.standards.example.invalid",),
    )
    assert host_is_allowlisted("research.example.invalid", 443, policy)
    assert host_is_allowlisted("v1.standards.example.invalid", 443, policy)
    assert not host_is_allowlisted("evilresearch.example.invalid", 443, policy)
    assert not host_is_allowlisted("standards.example.invalid", 443, policy)


def test_allowlist_rejects_universal_wildcard_and_too_many_domains():
    with pytest.raises(ValueError):
        validate_domain_allowlist(("*",))
    with pytest.raises(ValueError):
        validate_domain_allowlist(tuple(f"d{i}.example.invalid" for i in range(21)))


def test_unicode_hosts_normalize_deterministically():
    one = validate_domain_allowlist(("r\u00e9search.example.invalid",))
    two = validate_domain_allowlist(("xn--rsearch-bya.example.invalid",))
    assert one.exact_hosts == two.exact_hosts
