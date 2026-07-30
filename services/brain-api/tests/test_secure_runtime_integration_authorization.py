from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    AUTH_ID,
    AUTH_SCOPE,
    CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    PROGRAM_STATE,
    load_json,
)


def test_aion230_sri_authorization_is_active_and_single_use() -> None:
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")
    example = load_json(
        "examples/secure-runtime-integration/local-operator-runtime-authorization.json"
    )

    for payload in (auth, example):
        assert payload["program_id"] == PROGRAM_ID
        assert payload["authorization_transaction_id"] == AUTH_ID
        assert payload["approval_record_id"] == AUTH_ID
        assert payload["candidate_id"] == "authenticated-local-operator-runtime-foundation-core"
        assert payload["workstream"] == "secure-runtime-foundation"
        assert payload["implementation_task"] == IMPLEMENTATION_TASK
        assert payload["formal_closeout_task"] == CLOSEOUT_TASK
        assert payload["authorization_scope"] == AUTH_SCOPE
        assert payload["authorization_transaction_approved"] is True
        assert payload["explicit_approval_record_approval"] is True
        assert payload["implementation_authorization_approved"] is True
        assert payload["implementation_go_status"] is True
        assert payload["implementation_no_go_status"] is False
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
        assert payload["active_sri_implementation_authorization_count"] == 1
        assert payload["active_sri_implementation_authorization"] == AUTH_ID
        assert payload["active_sri_implementation_task"] == IMPLEMENTATION_TASK
        assert payload["program_state"] == PROGRAM_STATE

    assert auth["active_authorizations"] == [
        {
            "authorization_transaction_id": AUTH_ID,
            "implementation_task": IMPLEMENTATION_TASK,
            "formal_closeout_task": CLOSEOUT_TASK,
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
        }
    ]
    assert len(auth["records"]) == 1
    assert auth["records"][0]["authorization_transaction_id"] == AUTH_ID
    assert auth["records"][0]["created_by_task"] == "AION-230"
