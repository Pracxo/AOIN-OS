from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_capability_plan_matches_closed_manifest_without_execution() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.capability_plan.capability_code == "brain.think.simulate"
    assert fixture.capability_plan.risk_class.value == "medium"
    assert fixture.capability_plan.approval_required is True
    assert fixture.capability_plan.simulation_only is True
    assert fixture.capability_plan.actual_execution_available is False
    assert fixture.capability_plan.production_effect is False
