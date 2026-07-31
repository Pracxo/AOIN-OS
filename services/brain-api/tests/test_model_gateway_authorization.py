from secure_runtime_aion232_test_helpers import (
    AION232,
    MODEL_GATEWAY_SCOPE,
    PASS_DECISION,
    active_authorization_record,
    authorization,
)


def test_aion232_authorization_is_exact_and_sole_active_sri_authorization() -> None:
    payload = authorization()
    record = active_authorization_record()
    assert payload["active_sri_implementation_authorization_count"] == 1
    assert payload["active_sri_implementation_authorization"] == AION232
    assert payload["active_sri_implementation_task"] == "AION-233"
    assert record["authorization_transaction_id"] == AION232
    assert record["approval_record_id"] == AION232
    assert record["parent_authorization_transaction_id"] == "AION-230-SRI-0001"
    assert record["parent_evaluation_decision"] == PASS_DECISION
    assert record["candidate_id"] == "controlled-provider-neutral-model-gateway-core"
    assert record["workstream"] == "secure-runtime-model-gateway"
    assert record["implementation_task"] == "AION-233"
    assert record["formal_closeout_task"] == "AION-234"
    assert record["authorization_scope"] == MODEL_GATEWAY_SCOPE
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
