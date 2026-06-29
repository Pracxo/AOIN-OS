from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.connector_runtime import MockConnectorManifestService
from aion_brain.contracts.connector_runtime import MockConnectorManifest


def _manifest(**updates: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
    return payload


def test_mock_connector_manifest_accepts_preview_only_shape() -> None:
    manifest = MockConnectorManifest(**_manifest())
    result = MockConnectorManifestService().validate(manifest)

    assert result.valid is True
    assert result.normalized_manifest["connector_key"] == "mock.local.preview"


def test_mock_connector_manifest_rejects_runtime_enabling_shape() -> None:
    with pytest.raises(ValidationError):
        MockConnectorManifest(**_manifest(external_calls_required=True))
    with pytest.raises(ValidationError):
        MockConnectorManifest(**_manifest(credentials_required=True))
    with pytest.raises(ValidationError):
        MockConnectorManifest(**_manifest(routes_declared=[{"path": "/disabled"}]))
