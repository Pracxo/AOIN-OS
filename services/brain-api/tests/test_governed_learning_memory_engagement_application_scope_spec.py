from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_engagement_application_authorization as engauth

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE = (
    "governed_learning_memory_engagement_application_implemented_shadow_only_pending_closeout"
)
CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE = (
    "governed_learning_memory_controlled_local_continual_learning_pilot_"
    "authorized_not_implemented"
)
CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE = (
    "governed_learning_memory_controlled_local_continual_learning_pilot_"
    "implemented_completed_pending_final_closeout"
)


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_authorization_scope_and_source_are_recorded_not_created():
    auth = load_json("examples/governed-learning-memory/engagement-application-authorization.json")
    program = load_json("docs/governed-learning-memory/program-ledger.json")
    assert auth["authorization_scope"] == engauth.ENGAGEMENT_AUTHORIZATION_SCOPE
    assert auth["implementation_task"] == "AION-226"
    source_exists = [
        (REPO_ROOT / rel).exists() for rel in auth["source_scope_recorded_not_created"]
    ]
    if program["program_state"] in {
        ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
        CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
        CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
    }:
        assert all(source_exists)
    else:
        assert not any(source_exists)
