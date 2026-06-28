from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_action_authorization_services() -> None:
    container = kernel_container()

    assert container.dry_run_action_authorization_service is not None
    assert container.action_authorization_audit_service is not None
    assert container.action_authorization_query_service is not None

    checks = KernelDiagnostics(container).run()
    names = {check.name for check in checks}
    assert "action_authorization_services_present" in names
    assert "action_authorization_execution_allowed" in names
