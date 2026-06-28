from __future__ import annotations

from aion_brain.auth_runtime import AuthRuntimeAuditService, AuthRuntimeGateService
from aion_brain.auth_runtime.mock_claims import MockClaimsPreviewService
from aion_brain.contracts.auth_runtime import AuthRuntimeAuditRequest, MockClaimsPreviewRequest
from tests.operator_action_fakes import FakeTelemetry


def test_visual_telemetry_emits_auth_runtime_events() -> None:
    telemetry = FakeTelemetry()
    AuthRuntimeGateService(telemetry_service=telemetry).status(["workspace:main"])
    MockClaimsPreviewService(telemetry_service=telemetry).preview(
        MockClaimsPreviewRequest(subject="local.operator", roles=["operator"])
    )
    AuthRuntimeAuditService(telemetry_service=telemetry).audit(
        AuthRuntimeAuditRequest(owner_scope=["workspace:main"])
    )

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in telemetry.events}
    assert "auth_runtime_status_checked" in event_types
    assert "mock_claims_preview_created" in event_types
    assert "auth_runtime_audit_completed" in event_types
    assert "auth_runtime_status" in node_types
    assert "mock_claims_preview" in node_types
    assert "auth_runtime_audit" in node_types
