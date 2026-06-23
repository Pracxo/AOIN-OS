"""Kernel wiring tests for module mock runtime."""

from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_module_mock_runtime_components() -> None:
    container = kernel_container()
    checks = KernelDiagnostics(container).run()
    by_name = {check.name: check for check in checks}

    assert by_name["module_mock_repository_present"].status == "passed"
    assert by_name["module_mock_profile_service_present"].status == "passed"
    assert by_name["module_mock_simulator_present"].status == "passed"
    assert by_name["module_mock_query_service_present"].status == "passed"
