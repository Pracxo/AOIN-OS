from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def _manifest_payload() -> dict[str, object]:
    return {
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


def test_connector_runtime_api_endpoints_are_preview_only() -> None:
    client = TestClient(create_app(kernel_container()))

    status = client.get("/brain/connector-runtime/status", params={"scope": "workspace:main"})
    manifest = client.post(
        "/brain/connector-runtime/mock-manifest/validate",
        json=_manifest_payload(),
    )
    egress = client.post(
        "/brain/connector-runtime/egress-preview",
        json={
            "connector_key": "mock.local.preview",
            "owner_scope": ["workspace:main"],
            "payload_summary": {"fields": ["case_id"]},
        },
    )
    ingress = client.post(
        "/brain/connector-runtime/ingress-preview",
        json={
            "connector_key": "mock.local.preview",
            "owner_scope": ["workspace:main"],
            "response_summary": {"fields": ["case_id"]},
        },
    )
    audit = client.post(
        "/brain/connector-runtime/audit",
        json={"owner_scope": ["workspace:main"], "include_examples": True},
    )

    assert status.status_code == 200
    assert status.json()["connector_runtime_enabled"] is False
    assert status.json()["connector_external_calls_enabled"] is False
    assert manifest.status_code == 200
    assert manifest.json()["valid"] is True
    assert manifest.json()["normalized_manifest"]["external_calls_required"] is False
    assert egress.status_code == 200
    assert egress.json()["egress_allowed"] is False
    assert egress.json()["external_call_allowed"] is False
    assert ingress.status_code == 200
    assert ingress.json()["trusted"] is False
    assert audit.status_code == 200
    assert audit.json()["status"] == "passed"
