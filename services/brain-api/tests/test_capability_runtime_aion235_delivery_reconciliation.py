from __future__ import annotations

from operator_console_integration_test_support import program_ledger


def test_aion235_delivery_reconciled_after_operator_evaluation_pass():
    record = program_ledger()["aion_235_record"]
    assert record["feature_commits"] == ["03a86f5314b8e79e0d77e2657769be0b15f1c450"]
    assert record["pull_requests"] == [154]
    assert record["merge_commits"] == ["39eff73b76f8b68a956f0a852bf8fbd71d36654d"]
    assert record["ci_result"] == "pass"
    assert record["evaluation_id"] == "AION-SRIPE-003"
