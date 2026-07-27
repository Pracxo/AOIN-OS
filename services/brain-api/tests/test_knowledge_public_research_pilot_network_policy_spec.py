from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_network_policy_stays_runtime_disabled() -> None:
    plan = load_json("examples/knowledge-intelligence/public-research-pilot-plan.json")
    network = load_json(
        "operator-console-static/demo-data/"
        "knowledge-intelligence-public-research-pilot-network-policy.json"
    )
    assert {
        candidate["scheme"] for candidate in plan["explicit_source_candidates"]
    } == {"https"}
    assert plan["allowed_methods"] == ["GET", "HEAD"]
    assert network["allowlist_required"] is True
    assert network["https_only"] is True
    assert network["crawler_enabled"] is False
    assert public_auth()["public_network_fetch_enabled"] is False
    assert public_auth()["operator_invoked_public_https_fetch_available"] is True
    assert public_auth()["system_dns_resolution_available"] is True
    assert public_auth()["system_http_transport_available"] is True
