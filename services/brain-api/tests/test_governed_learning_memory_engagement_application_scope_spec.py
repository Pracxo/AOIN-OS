from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_engagement_application_authorization as engauth

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_authorization_scope_and_source_are_recorded_not_created():
    auth = load_json("examples/governed-learning-memory/engagement-application-authorization.json")
    assert auth["authorization_scope"] == engauth.ENGAGEMENT_AUTHORIZATION_SCOPE
    assert auth["implementation_task"] == "AION-226"
    for rel in auth["source_scope_recorded_not_created"]:
        assert not (REPO_ROOT / rel).exists()
