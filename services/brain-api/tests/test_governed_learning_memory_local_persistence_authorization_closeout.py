from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_engagement_application_authorization as engauth

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_aion223_authorization_is_closed_and_aion225_is_active():
    _, auth = engauth.validate_authorization_ledgers(REPO_ROOT)
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
    assert child["authorization_active"] is True
    assert child["implementation_task"] == "AION-226"
