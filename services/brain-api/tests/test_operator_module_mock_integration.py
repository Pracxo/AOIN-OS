"""Operator integration for module mock runtime."""

from __future__ import annotations

from aion_brain.module_mock_runtime import ModuleMockSimulator
from aion_brain.operator.action_center import ActionCenterService
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import invocation_request, settings
from tests.module_mock_helpers import repository as mock_repository
from tests.operator_fakes import FakeTelemetry
from tests.operator_fakes import repository as operator_repository


def test_operator_surfaces_blocked_module_mock_run_and_high_finding() -> None:
    module_mock_repository = mock_repository()
    simulator = ModuleMockSimulator(module_mock_repository, AllowPolicy(), settings=settings())
    simulator.invoke(invocation_request("missing-binding"))
    service = ActionCenterService(
        operator_repository(),
        AllowPolicy(),
        FakeTelemetry(),
        module_mock_repository=module_mock_repository,
    )

    items = service.build_action_items(["workspace:main"])

    recommended = {item.recommended_action for item in items}
    assert "review_module_mock_run" in recommended
    assert "review_module_mock_finding" in recommended
