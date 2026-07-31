from aion234_test_support import capability_auth, load_harness


def test_capability_runtime_authorization_identity_and_scope() -> None:
    h = load_harness()
    auth = capability_auth()
    assert auth["authorization_transaction_id"] == "AION-234-SRI-0003"
    assert auth["parent_authorization_transaction_id"] == "AION-232-SRI-0002"
    assert auth["parent_evaluation_decision"] == h.DECISION_PASS
    assert auth["implementation_task"] == "AION-235"
    assert auth["formal_closeout_task"] == "AION-236"
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False
