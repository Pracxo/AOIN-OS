from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_dispatch_is_deterministic_and_simulation_only() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.dispatch.status.value == "simulated"
    assert fixture.dispatch.simulation_only is True
    assert fixture.dispatch.actual_execution_performed is False
    assert fixture.dispatch.external_call_performed is False
    assert fixture.dispatch.provider_call_performed is False
    assert fixture.dispatch.connector_call_performed is False
    assert fixture.dispatch.tool_execution_performed is False
    assert fixture.dispatch.production_effect is False
