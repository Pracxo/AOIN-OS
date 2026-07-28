from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT


def test_aion222_delivery_is_reconciled_into_aion223_authorization_closeout() -> None:
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

    expected_delivery = {
        "task_id": "AION-222",
        "branch": "phase/governed-learning-memory-promotion-transaction-core",
        "feature_commits": ["e415cc397b9aec70f8b3d19285f5fdd315048731"],
        "pull_requests": [138],
        "merge_commits": ["b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"],
        "ci_result": "pass",
        "completion_timestamp": "2026-07-28T09:00:39Z",
        "authorization_transaction": "AION-221-GLM-0001",
        "authorization_state": "consumed_by_AION-222_closed_by_AION-223",
        "next_task": "AION-223",
        "runtime_state": "promotion_transaction_core_implemented_dry_run_in_memory_write_disabled",
        "evaluation_id": "AION-GLMPE-001",
        "evaluation_decision": (
            "PROMOTION_TRANSACTION_OPERATOR_EVALUATION_PASS_RECOMMEND_LOCAL_"
            "APPEND_ONLY_KNOWLEDGE_PERSISTENCE_AUTHORIZATION"
        ),
    }
    for key, expected in expected_delivery.items():
        assert ledger["aion_222_delivery"][key] == expected

    closed = next(
        record
        for record in authorization["records"]
        if record["authorization_transaction_id"] == "AION-221-GLM-0001"
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_consumed_by_task"] == "AION-222"
    assert closed["authorization_consumed_by_prs"] == [138]
    assert closed["authorization_consumed_by_feature_commits"] == [
        "e415cc397b9aec70f8b3d19285f5fdd315048731"
    ]
    assert closed["authorization_consumed_by_merge_commits"] == [
        "b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"
    ]
    assert closed["authorization_closed_by_task"] == "AION-223"
