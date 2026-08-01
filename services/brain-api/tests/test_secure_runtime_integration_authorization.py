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


def test_aion230_sri_authorization_is_closed_and_current_aion232_auth_is_single_active() -> None:
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")
    example = load_json(
        "examples/secure-runtime-integration/local-operator-runtime-authorization.json"
    )

    assert auth["program_id"] == PROGRAM_ID
    current_auth = auth["authorization_transaction_id"]
    assert current_auth in {"AION-234-SRI-0003", "AION-236-SRI-0004"}
    if current_auth == "AION-236-SRI-0004":
        assert auth["approval_record_id"] == "AION-236-SRI-0004"
        assert auth["candidate_id"] == "controlled-local-operator-console-integration-core"
        assert auth["workstream"] == "secure-runtime-operator-console-integration"
        assert auth["implementation_task"] == "AION-237"
        assert auth["formal_closeout_task"] == "AION-238"
    else:
        assert auth["approval_record_id"] == "AION-234-SRI-0003"
        assert auth["candidate_id"] == "controlled-sandboxed-reference-capability-runtime-core"
        assert auth["workstream"] == "secure-runtime-sandboxed-capability-runtime"
        assert auth["implementation_task"] == "AION-235"
        assert auth["formal_closeout_task"] == "AION-236"
    assert auth["authorization_transaction_approved"] is True
    assert auth["explicit_approval_record_approval"] is True
    assert auth["implementation_authorization_approved"] is True
    assert auth["implementation_go_status"] is True
    assert auth["implementation_no_go_status"] is False
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False
    assert auth["active_sri_implementation_authorization_count"] == 1
    active_state = (
        auth["active_sri_implementation_authorization"],
        auth["active_sri_implementation_task"],
        auth["formal_closeout_task"],
    )
    assert active_state in {
        ("AION-234-SRI-0003", "AION-235", "AION-236"),
        ("AION-236-SRI-0004", "AION-237", "AION-238"),
    }
    assert auth["program_state"] in {
        PROGRAM_STATE,
        "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented",
        "operator_console_integrated_local_runtime_implemented_pending_final_evaluation",
    }

    assert auth["active_authorizations"] == [
        {
            "authorization_transaction_id": active_state[0],
            "implementation_task": active_state[1],
            "formal_closeout_task": active_state[2],
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
        }
    ]
    assert len(auth["records"]) >= 3
    aion230 = next(
        item for item in auth["records"] if item["authorization_transaction_id"] == AUTH_ID
    )
    assert aion230["created_by_task"] == "AION-230"
    assert aion230["implementation_task"] == IMPLEMENTATION_TASK
    assert aion230["formal_closeout_task"] == CLOSEOUT_TASK
    assert aion230["authorization_scope"] == AUTH_SCOPE
    assert aion230["authorization_active"] is False
    assert aion230["authorization_consumed"] is True
    assert aion230["authorization_expired"] is True
    assert aion230["authorization_reusable"] is False
    assert aion230["authorization_consumed_by_task"] == IMPLEMENTATION_TASK
    assert aion230["authorization_closed_by_task"] == CLOSEOUT_TASK
    assert aion230["runtime_foundation_evaluation_id"] == "AION-SRIPE-001"

    aion232 = next(
        item
        for item in auth["records"]
        if item["authorization_transaction_id"] == "AION-232-SRI-0002"
    )
    assert aion232["authorization_active"] is False
    assert aion232["authorization_consumed"] is True
    assert aion232["authorization_expired"] is True
    assert aion232["authorization_reusable"] is False
    assert aion232["authorization_consumed_by_task"] == "AION-233"
    assert aion232["authorization_closed_by_task"] == "AION-234"

    assert example["program_id"] == PROGRAM_ID
    assert example["authorization_transaction_id"] == AUTH_ID
    assert example["approval_record_id"] == AUTH_ID
    assert example["candidate_id"] == "authenticated-local-operator-runtime-foundation-core"
    assert example["workstream"] == "secure-runtime-foundation"
    assert example["implementation_task"] == IMPLEMENTATION_TASK
    assert example["formal_closeout_task"] == CLOSEOUT_TASK
    assert example["authorization_scope"] == AUTH_SCOPE
    assert example["authorization_transaction_approved"] is True
    assert example["explicit_approval_record_approval"] is True
    assert example["implementation_authorization_approved"] is True
    assert example["implementation_go_status"] is True
    assert example["implementation_no_go_status"] is False
    assert example["authorization_active"] is True
    assert example["authorization_consumed"] is False
    assert example["authorization_expired"] is False
    assert example["authorization_reusable"] is False
