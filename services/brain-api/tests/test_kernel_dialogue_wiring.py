from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_dialogue_checks() -> None:
    container = kernel_container()

    checks = {check.name: check for check in container.diagnostics.run()}

    assert checks["dialogue_enabled"].status == "passed"
    assert checks["response_composer_enabled"].status == "passed"
    assert checks["clarification_loop_enabled"].status == "passed"
    assert checks["dialogue_services_present"].status == "passed"
