from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_scope_and_identity_are_exact() -> None:
    auth = public_auth()
    assert auth["candidate_id"] == "controlled-public-research-verified-knowledge-pilot"
    assert auth["workstream"] == "knowledge-intelligence-controlled-public-research-pilot"
    assert auth["authorization_scope"] == (
        "operator-invoked-allowlisted-public-https-fetch-dns-pinning-"
        "integrated-research-verified-candidate-pilot-operator-review-abstention-core"
    )
    assert auth["controlled_public_research_pilot_authorized"] is True
    assert auth["controlled_public_research_pilot_implemented"] is True
    assert auth["controlled_public_research_pilot_state"] == (
        "implemented_operator_invoked_bounded_public_https_integrated_pipeline_"
        "persistent_write_disabled"
    )
