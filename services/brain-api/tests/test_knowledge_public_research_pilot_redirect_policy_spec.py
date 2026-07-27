from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_redirect_policy_requires_revalidation() -> None:
    auth = public_auth()
    capabilities = auth["authorized_capabilities"]
    assert capabilities["manual_redirect_handling_approved"] is True
    assert capabilities["redirect_destination_revalidation_approved"] is True
    assert capabilities["redirect_scheme_downgrade_rejection_approved"] is True
    assert capabilities["redirect_loop_detection_approved"] is True
