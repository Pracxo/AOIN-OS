"""Golden Path assertion engine tests."""

from aion_brain.golden_path.assertions import AssertionEngine


def test_assertion_engine_status_equals_passes() -> None:
    result = AssertionEngine().evaluate_assertion(
        {
            "assertion_key": "step.passed",
            "assertion_type": "status_equals",
            "path": "steps.boot.status",
            "expected": "passed",
            "severity": "high",
        },
        {
            "golden_path_run_id": "run-1",
            "golden_path_scenario_id": "scenario-1",
            "steps": {"boot": {"status": "passed"}},
        },
    )

    assert result.status == "passed"


def test_assertion_engine_unknown_type_fails_closed() -> None:
    result = AssertionEngine().evaluate_assertion(
        {"assertion_key": "unknown", "assertion_type": "execute_code"},
        {"golden_path_run_id": "run-1", "golden_path_scenario_id": "scenario-1"},
    )

    assert result.status == "failed"
    assert result.assertion_type == "generic"


def test_assertion_engine_detects_external_call_flag() -> None:
    result = AssertionEngine().evaluate_assertion(
        {"assertion_key": "no.external", "assertion_type": "no_external_call"},
        {
            "golden_path_run_id": "run-1",
            "golden_path_scenario_id": "scenario-1",
            "external_calls": True,
        },
    )

    assert result.status == "failed"


def test_assertion_engine_detects_secret_like_payload() -> None:
    result = AssertionEngine().evaluate_assertion(
        {"assertion_key": "no.secret", "assertion_type": "no_secret"},
        {
            "golden_path_run_id": "run-1",
            "golden_path_scenario_id": "scenario-1",
            "payload": {"api_key": "redacted"},
        },
    )

    assert result.status == "failed"


def test_assertion_engine_detects_hidden_reasoning_marker() -> None:
    result = AssertionEngine().evaluate_assertion(
        {"assertion_key": "no.hidden", "assertion_type": "no_hidden_reasoning"},
        {
            "golden_path_run_id": "run-1",
            "golden_path_scenario_id": "scenario-1",
            "payload": {"hidden_reasoning": "not allowed"},
        },
    )

    assert result.status == "failed"
