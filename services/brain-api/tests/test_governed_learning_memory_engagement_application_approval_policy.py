from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_approval_policy_requires_existing_approvals():
    auth = load_json("examples/governed-learning-memory/engagement-application-authorization.json")
    policy = auth["approval_policy"]
    assert policy["accept_existing_approvals_only"] is True
    assert policy["runtime_can_create_approval_request"] is False
    assert policy["runtime_can_create_approval_decision"] is False
    assert policy["elevated_risk_minimum_independent_approvers"] == 2
