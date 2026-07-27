from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_public_research_pilot_tls_policy_is_certificate_and_hostname_bound() -> None:
    exchange = load_json(
        "examples/knowledge-intelligence/public-research-pilot-http-exchange.json"
    )
    dns_resolution = load_json(
        "examples/knowledge-intelligence/public-research-pilot-dns-resolution.json"
    )
    assert exchange["tls_certificate_verified"] is True
    assert exchange["tls_hostname_verified"] is True
    assert exchange["tls_sni_bound_to_original_host"] is True
    assert exchange["pinned_peer_address"] in dns_resolution["validated_public_addresses"]
