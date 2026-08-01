from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_request_idempotency_and_changed_replay_verified():
    item = assert_scenario_passes("request_idempotency_and_changed_replay")

    assert {check["name"] for check in item["checks"]} >= {
        "exact_replay_returns_existing_result",
        "exact_replay_no_second_execution",
        "changed_replay_rejected",
    }
