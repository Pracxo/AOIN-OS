from __future__ import annotations

from aion_brain.connector_sandbox.denials import ConnectorSandboxDenialService


def test_connector_sandbox_denials_cover_future_runtime_capabilities() -> None:
    service = ConnectorSandboxDenialService()

    assert service.denial_for("connector.sandbox.network.egress") is not None
    assert service.denial_for("connector.sandbox.runtime.execute") is not None
    assert service.denial_for("connector.sandbox.readiness.preview") is None
    assert all(
        service.denial_for(capability)["runtime_execution_allowed"] is False
        for capability in service.denied_capabilities()
        if service.denial_for(capability) is not None
    )
