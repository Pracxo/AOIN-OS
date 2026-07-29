from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_engagement_application_authorization as engauth
from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_aion223_authorization_is_closed_and_aion225_is_active():
    _, auth = engauth.validate_authorization_ledgers(REPO_ROOT)
    program_state = load_json("docs/governed-learning-memory/program-ledger.json")[
        "program_state"
    ]
    records = auth["records"]
    parent = next(
        item for item in records if item["authorization_transaction_id"] == "AION-223-GLM-0002"
    )
    child = next(
        item for item in records if item["authorization_transaction_id"] == "AION-225-GLM-0003"
    )
    assert parent["authorization_active"] is False
    assert parent["authorization_consumed"] is True
    assert parent["authorization_expired"] is True
    assert parent["authorization_reusable"] is False
    if program_state in {
        CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
        CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
    }:
        assert child["authorization_active"] is False
        assert child["authorization_consumed"] is True
        assert child["authorization_expired"] is True
        assert child["authorization_reusable"] is False
        assert auth["active_authorizations"] == ["AION-227-GLM-0004"]
    else:
        assert child["authorization_active"] is True
    assert child["implementation_task"] == "AION-226"
