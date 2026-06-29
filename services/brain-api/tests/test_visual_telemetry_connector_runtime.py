from __future__ import annotations

from aion_brain.connector_runtime import (
    ConnectorEgressPreviewService,
    ConnectorIngressPreviewService,
    ConnectorRuntimeAuditService,
    ConnectorRuntimeGateService,
    MockConnectorManifestService,
)
from aion_brain.contracts.connector_runtime import (
    ConnectorEgressPreviewRequest,
    ConnectorIngressPreviewRequest,
    ConnectorRuntimeAuditRequest,
    MockConnectorManifest,
)
from tests.operator_action_fakes import FakeTelemetry


def test_visual_telemetry_emits_connector_runtime_events() -> None:
    telemetry = FakeTelemetry()
    ConnectorRuntimeGateService(telemetry_service=telemetry).status(["workspace:main"])
    MockConnectorManifestService(telemetry_service=telemetry).validate(
        MockConnectorManifest(
            connector_key="mock.local.preview",
            name="Mock Local Preview",
            description="Mock-only connector manifest.",
            version="0.0.0-preview",
            owner_scope=["workspace:main"],
            connector_type="mock",
            supported_modes=["dry_run"],
            declared_capabilities=[],
            required_policy_actions=[],
            required_scopes=[],
            sandbox_required=True,
            dry_run_supported=True,
            external_calls_required=False,
            credentials_required=False,
            routes_declared=[],
        )
    )
    ConnectorEgressPreviewService(telemetry_service=telemetry).preview(
        ConnectorEgressPreviewRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
        )
    )
    ConnectorIngressPreviewService(telemetry_service=telemetry).preview(
        ConnectorIngressPreviewRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
        )
    )
    ConnectorRuntimeAuditService(telemetry_service=telemetry).audit(
        ConnectorRuntimeAuditRequest(owner_scope=["workspace:main"])
    )

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in telemetry.events}
    assert "connector_runtime_status_checked" in event_types
    assert "connector_manifest_validated" in event_types
    assert "connector_egress_preview_created" in event_types
    assert "connector_ingress_preview_created" in event_types
    assert "connector_runtime_audit_completed" in event_types
    assert "connector_runtime_status" in node_types
    assert "connector_manifest" in node_types
    assert "connector_egress_preview" in node_types
    assert "connector_ingress_preview" in node_types
    assert "connector_runtime_audit" in node_types
