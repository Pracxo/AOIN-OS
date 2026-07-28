from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION221_AUTHORIZATION_ID,
    AION223_AUTHORIZATION_ID,
    PASS_DECISION,
)
from test_governed_learning_memory_program_authorization import load_json


def test_aion221_closeout_is_consumed_expired_and_non_reusable() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    closed = next(
        x for x in auth["records"] if x["authorization_transaction_id"] == AION221_AUTHORIZATION_ID
    )
    assert (
        closed["authorization_active"] is False
        and closed["authorization_consumed"] is True
        and closed["authorization_expired"] is True
        and closed["authorization_reusable"] is False
    )
    assert closed["authorization_consumed_by_task"] == "AION-222" and closed[
        "authorization_consumed_by_prs"
    ] == [138]
    assert closed["authorization_consumed_by_feature_commits"] == [
        "e415cc397b9aec70f8b3d19285f5fdd315048731"
    ] and closed["authorization_consumed_by_merge_commits"] == [
        "b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"
    ]
    assert (
        closed["authorization_closed_by_task"] == "AION-223"
        and closed["promotion_transaction_operator_evaluation_decision"] == PASS_DECISION
    )
    assert auth["active_authorizations"] == [AION223_AUTHORIZATION_ID]
