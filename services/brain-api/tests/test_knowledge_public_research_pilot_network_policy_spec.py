from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_network_policy_disabled_before_implementation() -> None:
    plan = load_json("examples/knowledge-intelligence/public-research-pilot-plan.json")
    network = load_json(
        "operator-console-static/demo-data/"
        "knowledge-intelligence-public-research-pilot-network-policy.json"
    )
    assert plan["allowed_schemes"] == ["https"]
    assert plan["allowed_methods"] == ["GET", "HEAD"]
    assert network["explicit_allowlist_required"] is True
    assert network["dns_pinning_required"] is True
    assert public_auth()["public_network_fetch_enabled"] is False
    assert public_auth()["operator_invoked_public_https_fetch_available"] is False
