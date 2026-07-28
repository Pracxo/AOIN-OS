from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT


def test_aion221_authorization_is_closed_and_aion222_delivery_reconciled():
    ledger = json.loads(
        (REPO_ROOT / "docs/governed-learning-memory/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    authorization = json.loads(
        (REPO_ROOT / "docs/governed-learning-memory/authorization-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["aion_221_delivery"]["pull_requests"] == [137]
    assert ledger["aion_222_delivery"]["pull_requests"] == [138]
    assert ledger["aion_222_delivery"]["feature_commits"] == [
        "e415cc397b9aec70f8b3d19285f5fdd315048731"
    ]
    assert ledger["aion_222_delivery"]["merge_commits"] == [
        "b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"
    ]
    assert ledger["aion_222_delivery"]["completion_timestamp"] == "2026-07-28T09:00:39Z"
    closed = next(
        item
        for item in authorization["records"]
        if item["authorization_transaction_id"] == "AION-221-GLM-0001"
    )
    assert closed["implementation_task"] == "AION-222"
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_closed_by_task"] == "AION-223"
