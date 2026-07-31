from __future__ import annotations

from secure_runtime_aion232_test_helpers import program


def test_aion232_delivery_reconciliation_is_recorded_after_aion233() -> None:
    record = program()["aion_232_record"]
    assert record["harness_commit"] == "6e0618b77e22ee45961b9660e6987af73436e3f7"
    assert record["closeout_commit"] == "58ca782263b0393d3b47bdedc5d8fbb4e6a7ad4a"
    assert record["feature_commits"] == [
        "6e0618b77e22ee45961b9660e6987af73436e3f7",
        "58ca782263b0393d3b47bdedc5d8fbb4e6a7ad4a",
    ]
    assert record["pull_requests"] == [150]
    assert record["merge_commits"] == [
        "490fc7070fd4f46d49d3cbe8fde28c006f5b5ed8",
    ]
    assert record["ci_result"] == "pass"
    assert record["completion_timestamp"] == "2026-07-31T03:41:13Z"
    assert record["authorization_state"] == "active_for_AION-233_formal_closeout_AION-234"
