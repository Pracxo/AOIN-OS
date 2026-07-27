from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_public_research_pilot_tls_policy_is_certificate_and_hostname_bound() -> None:
    exchange = load_json("examples/knowledge-intelligence/public-research-pilot-http-exchange.json")
    dns_resolution = load_json(
        "examples/knowledge-intelligence/public-research-pilot-dns-resolution.json"
    )
    assert exchange["tls_protocol_version"] == "TLSv1.3"
    assert exchange["certificate_subject_fingerprint"]
    assert exchange["certificate_issuer_fingerprint"]
    assert exchange["hostname_fingerprint"] == dns_resolution["host_fingerprint"]
    assert exchange["destination_resolution_fingerprint"] == dns_resolution[
        "resolution_fingerprint"
    ]
    assert exchange["peer_address_fingerprint"] in dns_resolution[
        "address_fingerprints"
    ]
