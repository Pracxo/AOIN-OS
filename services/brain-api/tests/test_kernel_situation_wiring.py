from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_situation_services_and_diagnostics() -> None:
    container = kernel_container()
    checks = {check.name for check in container.diagnostics.run()}

    assert container.situation_service is not None
    assert container.situation_projector is not None
    assert "situations_enabled" in checks
    assert "situation_services_present" in checks
