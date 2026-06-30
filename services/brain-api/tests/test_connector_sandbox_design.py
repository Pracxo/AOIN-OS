from __future__ import annotations

from aion_brain.connector_sandbox.design import ConnectorSandboxDesignService


def test_connector_sandbox_design_boundary_is_disabled() -> None:
    boundary = ConnectorSandboxDesignService().boundary()

    assert boundary.sandbox_boundary_id == "connector-sandbox-boundary-aion-112"
    assert boundary.runtime_execution_allowed is False
    assert boundary.filesystem_access_allowed is False
    assert boundary.network_access_allowed is False
    assert boundary.credential_access_allowed is False
    assert boundary.token_access_allowed is False
    assert boundary.process_spawn_allowed is False
    assert boundary.dynamic_import_allowed is False
    assert boundary.package_install_allowed is False
    assert boundary.connector_activation_allowed is False
    assert boundary.audit_required is True
    assert boundary.provenance_required is True
