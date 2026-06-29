from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.connector_runtime import (
    ConnectorEgressPreviewRequest,
    ConnectorEgressPreviewResult,
    ConnectorIngressPreviewResult,
    ConnectorRuntimeAuditRequest,
    ConnectorRuntimeAuditResult,
    ConnectorRuntimeStatus,
    MockConnectorManifest,
    MockConnectorManifestValidationResult,
    utc_now,
)


def test_connector_runtime_status_requires_hard_off_flags() -> None:
    status = ConnectorRuntimeStatus(
        status_id="connector-runtime-status-test",
        connector_runtime_enabled=False,
        connector_mock_preview_enabled=True,
        connector_egress_preview_enabled=True,
        connector_ingress_preview_enabled=True,
        connector_external_calls_enabled=False,
        connector_credentials_enabled=False,
        connector_token_storage_enabled=False,
        connector_activation_enabled=False,
        connector_route_registration_enabled=False,
        blockers=[],
        warnings=[],
        metadata={"mock_only": True},
        created_at=utc_now(),
    )

    assert status.connector_runtime_enabled is False
    assert status.connector_external_calls_enabled is False

    with pytest.raises(ValidationError):
        ConnectorRuntimeStatus(
            **status.model_copy(update={"connector_external_calls_enabled": True}).model_dump()
        )


def test_mock_connector_manifest_rejects_unsafe_declarations() -> None:
    manifest = MockConnectorManifest(
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
    with pytest.raises(ValidationError):
        MockConnectorManifest(
            **manifest.model_copy(update={"external_calls_required": True}).model_dump()
        )
    with pytest.raises(ValidationError):
        MockConnectorManifest(
            **manifest.model_copy(update={"credentials_required": True}).model_dump()
        )
    with pytest.raises(ValidationError):
        MockConnectorManifest(
            **manifest.model_copy(update={"routes_declared": [{"path": "/disabled"}]}).model_dump()
        )

    result = MockConnectorManifestValidationResult(
        connector_manifest_validation_id="connector-manifest-validation-test",
        connector_key=manifest.connector_key,
        status="preview",
        valid=True,
        external_calls_required=False,
        credentials_required=False,
        routes_declared_count=0,
        blockers=[],
        warnings=[],
        normalized_manifest={"connector_key": manifest.connector_key},
        metadata={"mock_only": True},
        created_at=utc_now(),
    )

    assert result.status == "preview"
    assert result.valid is True

    with pytest.raises(ValidationError):
        MockConnectorManifestValidationResult(
            **result.model_copy(update={"external_calls_required": True}).model_dump()
        )


def test_connector_preview_contracts_remain_blocked_and_untrusted() -> None:
    request = ConnectorEgressPreviewRequest(
        connector_key="mock.local.preview",
        owner_scope=["workspace:main"],
    )
    egress = ConnectorEgressPreviewResult(
        connector_egress_preview_id="connector-egress-preview-test",
        trace_id=request.trace_id,
        connector_key=request.connector_key,
        status="blocked",
        egress_allowed=False,
        external_call_allowed=False,
        credentials_present=False,
        blocked_fields=[],
        blockers=[],
        warnings=[],
        redacted_payload_summary={},
        metadata={"mock_only": True},
        created_at=utc_now(),
    )
    ingress = ConnectorIngressPreviewResult(
        connector_ingress_preview_id="connector-ingress-preview-test",
        connector_key=request.connector_key,
        status="preview",
        trusted=False,
        provenance_required=True,
        redaction_applied=True,
        prompt_injection_scan_required=True,
        normalized_response_summary={},
        blockers=[],
        warnings=[],
        metadata={"mock_only": True},
        created_at=utc_now(),
    )

    assert egress.egress_allowed is False
    assert ingress.trusted is False

    with pytest.raises(ValidationError):
        ConnectorEgressPreviewResult(
            **egress.model_copy(update={"egress_allowed": True}).model_dump()
        )
    with pytest.raises(ValidationError):
        ConnectorIngressPreviewResult(**ingress.model_copy(update={"trusted": True}).model_dump())


def test_connector_runtime_audit_result_requires_disabled_proofs() -> None:
    request = ConnectorRuntimeAuditRequest(owner_scope=["workspace:main"])
    result = ConnectorRuntimeAuditResult(
        connector_runtime_audit_id="connector-runtime-audit-test",
        trace_id=request.trace_id,
        status="passed",
        owner_scope=request.owner_scope,
        checks_run=["connector_runtime_disabled"],
        findings=[],
        runtime_disabled=True,
        external_calls_disabled=True,
        credentials_disabled=True,
        token_storage_disabled=True,
        activation_disabled=True,
        route_registration_disabled=True,
        network_clients_absent=True,
        provider_sdks_absent=True,
        created_at=utc_now(),
    )

    assert result.status == "passed"

    with pytest.raises(ValidationError):
        ConnectorRuntimeAuditResult(
            **result.model_copy(update={"credentials_disabled": False}).model_dump()
        )
