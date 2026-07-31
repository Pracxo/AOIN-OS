from secure_runtime_aion232_test_helpers import (
    AION231_FEATURE,
    AION231_MERGE,
    AION231_MERGED_AT,
    PASS_DECISION,
    program,
)


def test_aion231_delivery_reconciliation_records_pr_commits_ci_and_evaluation() -> None:
    record = program()["aion_231_record"]
    assert record["task_id"] == "AION-231"
    assert record["branch"] == "phase/secure-runtime-foundation"
    assert record["feature_commits"] == [AION231_FEATURE]
    assert record["pull_requests"] == [149]
    assert record["merge_commits"] == [AION231_MERGE]
    assert record["ci_result"] == "pass"
    assert record["completion_timestamp"] == AION231_MERGED_AT
    assert record["authorization_state"] == "consumed_by_AION-231_closed_by_AION-232"
    assert record["evaluation_id"] == "AION-SRIPE-001"
    assert record["evaluation_decision"] == PASS_DECISION
    assert record["evidence"]["every_prohibited_effect_zero"] is True
