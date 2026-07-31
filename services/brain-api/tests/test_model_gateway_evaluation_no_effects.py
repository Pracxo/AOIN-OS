from aion234_test_support import report, scenario


def test_zero_external_and_repository_boundaries_pass() -> None:
    payload = report()
    assert scenario(payload, "zero_external_and_production_effects")["passed"] is True
    assert (
        scenario(payload, "repository_release_and_runtime_registration_boundary")[
            "passed"
        ]
        is True
    )
    assert payload["network_calls"] == 0
    assert payload["connector_calls"] == 0
    assert payload["actual_tool_executions"] == 0
    assert payload["repository_unchanged"] is True
