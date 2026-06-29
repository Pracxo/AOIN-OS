from __future__ import annotations

from aion_brain.connector_runtime import ConnectorRuntimeGateService


def test_connector_runtime_gate_keeps_runtime_disabled() -> None:
    status = ConnectorRuntimeGateService().status(["workspace:main"])

    assert status.connector_runtime_enabled is False
    assert status.connector_external_calls_enabled is False
    assert status.connector_credentials_enabled is False
    assert status.connector_token_storage_enabled is False
    assert status.connector_activation_enabled is False
    assert status.connector_route_registration_enabled is False
