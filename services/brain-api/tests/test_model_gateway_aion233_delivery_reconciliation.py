from aion234_test_support import load_harness, load_json


def test_aion233_delivery_reconciled_after_operator_evaluation() -> None:
    h = load_harness()
    record = load_json("docs/secure-runtime-integration/program-ledger.json")["aion_233_record"]
    assert record["feature_commits"] == list(h.IMPLEMENTATION_FEATURE_COMMITS)
    assert record["pull_requests"] == [151, 152]
    assert record["merge_commits"] == list(h.IMPLEMENTATION_MERGE_COMMITS)
    assert record["ci_result"] == "pass"
    assert record["authorization_state"] == "consumed_by_AION-233_closed_by_AION-234"
    assert record["evaluation_decision"] == h.DECISION_PASS
