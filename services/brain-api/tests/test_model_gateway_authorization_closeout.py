from aion234_test_support import load_json


def test_aion232_authorization_closed_and_non_reusable() -> None:
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")
    closed = next(
        item
        for item in auth["records"]
        if item["authorization_transaction_id"] == "AION-232-SRI-0002"
    )
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert closed["authorization_consumed_by_task"] == "AION-233"
    assert closed["authorization_closed_by_task"] == "AION-234"
