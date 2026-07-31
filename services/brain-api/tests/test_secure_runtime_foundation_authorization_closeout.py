from secure_runtime_aion232_test_helpers import (
    AION231_FEATURE,
    AION231_MERGE,
    PASS_DECISION,
    closed_aion230_record,
)


def test_aion230_authorization_is_closed_consumed_expired_and_non_reusable() -> None:
    record = closed_aion230_record()
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_consumed_by_task"] == "AION-231"
    assert record["authorization_consumed_by_prs"] == [149]
    assert record["authorization_consumed_by_feature_commits"] == [AION231_FEATURE]
    assert record["authorization_consumed_by_merge_commits"] == [AION231_MERGE]
    assert record["authorization_closed_by_task"] == "AION-232"
    assert record["runtime_foundation_evaluation_id"] == "AION-SRIPE-001"
    assert record["runtime_foundation_evaluation_decision"] == PASS_DECISION
    assert record["evaluation_reusable"] is False
    assert record["evaluation_used_as_production_runtime_approval"] is False
    assert record["evaluation_used_as_provider_call_approval"] is False
