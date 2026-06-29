from __future__ import annotations

from aion_brain.connector_runtime import (
    ConnectorEgressPreviewService,
    ConnectorIngressPreviewService,
    ConnectorRuntimeGateService,
    ConnectorRuntimeQueryService,
    MockConnectorManifestService,
)
from aion_brain.contracts.connector_runtime import (
    ConnectorEgressPreviewRequest,
    ConnectorIngressPreviewRequest,
    MockConnectorManifest,
)


def _manifest(**updates: object) -> MockConnectorManifest:
    payload = {
        "connector_key": "mock.local.preview",
        "name": "Mock Local Preview",
        "description": "Mock-only connector manifest.",
        "version": "0.0.0-preview",
        "owner_scope": ["workspace:main"],
        "connector_type": "mock",
        "supported_modes": ["dry_run"],
        "declared_capabilities": [],
        "required_policy_actions": [],
        "required_scopes": [],
        "sandbox_required": True,
        "dry_run_supported": True,
        "external_calls_required": False,
        "credentials_required": False,
        "routes_declared": [],
    }
    payload.update(updates)
    return MockConnectorManifest(**payload)


def test_connector_runtime_gate_reports_disabled_status() -> None:
    status = ConnectorRuntimeGateService().status(["workspace:main"])

    assert status.connector_runtime_enabled is False
    assert status.connector_external_calls_enabled is False
    assert status.connector_credentials_enabled is False
    assert status.connector_token_storage_enabled is False
    assert status.connector_activation_enabled is False
    assert status.connector_route_registration_enabled is False
    assert status.blockers


def test_connector_runtime_query_delegates_to_gate() -> None:
    gate = ConnectorRuntimeGateService()
    status = ConnectorRuntimeQueryService(gate).status(["workspace:main"])

    assert status.status_id == "connector-runtime-status-local"


def test_mock_manifest_service_validates_preview_only_manifest() -> None:
    result = MockConnectorManifestService().validate(_manifest())

    assert result.status == "preview"
    assert result.valid is True
    assert result.blockers == []
    assert result.normalized_manifest["external_calls_required"] is False
    assert result.normalized_manifest["credentials_required"] is False


def test_connector_egress_preview_never_allows_external_call() -> None:
    result = ConnectorEgressPreviewService().preview(
        ConnectorEgressPreviewRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            payload_summary={"fields": ["case_id"]},
        )
    )

    assert result.status == "blocked"
    assert result.egress_allowed is False
    assert result.external_call_allowed is False
    assert result.credentials_present is False
    assert result.blockers


def test_connector_ingress_preview_remains_untrusted() -> None:
    result = ConnectorIngressPreviewService().preview(
        ConnectorIngressPreviewRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            response_summary={"fields": ["case_id"]},
        )
    )

    assert result.status == "preview"
    assert result.trusted is False
    assert result.provenance_required is True
    assert result.redaction_applied is True
    assert result.prompt_injection_scan_required is True
