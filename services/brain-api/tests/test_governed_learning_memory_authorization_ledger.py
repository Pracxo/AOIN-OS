from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION221_AUTHORIZATION_ID,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
)
from test_governed_learning_memory_program_authorization import (
    AUTH_ID,
    CANDIDATE_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    SCOPE,
    WORKSTREAM,
    load_json,
)


def test_authorization_ledger_has_single_active_aion224_authorization() -> None:
    ledger = load_json("docs/governed-learning-memory/authorization-ledger.json")
    if ledger["program_state"] == ENGAGEMENT_APPLICATION_AUTHORIZED_STATE:
        assert ledger["active_authorizations"] == ["AION-225-GLM-0003"]
        assert len(ledger["records"]) == 3
    else:
        assert ledger["active_authorizations"] == [AUTH_ID]
        assert len(ledger["records"]) == 2
    closed = next(
        item
        for item in ledger["records"]
        if item["authorization_transaction_id"] == AION221_AUTHORIZATION_ID
    )
    record = next(
        item for item in ledger["records"] if item["authorization_transaction_id"] == AUTH_ID
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert record["approval_record_id"] == AUTH_ID
    assert record["candidate_id"] == CANDIDATE_ID
    assert record["workstream"] == WORKSTREAM
    assert record["implementation_task"] == IMPLEMENTATION_TASK
    assert record["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
    assert record["authorization_scope"] == SCOPE
    if ledger["program_state"] == ENGAGEMENT_APPLICATION_AUTHORIZED_STATE:
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_closed_by_task"] == "AION-225"
    else:
        assert record["authorization_active"] is True
        assert record["authorization_consumed"] is False
        assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
