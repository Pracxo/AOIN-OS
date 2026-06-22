from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_decision_services_and_diagnostics() -> None:
    container = kernel_container()
    checks = {check.name for check in container.diagnostics.run()}

    assert container.decision_frame_service is not None
    assert container.option_evaluator is not None
    assert container.counterfactual_simulator is not None
    assert "decisions_enabled" in checks
    assert "decision_services_present" in checks
