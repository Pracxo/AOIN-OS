from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_connector_runtime_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.connector_runtime.status(["workspace:main"])
    client.connector_runtime.validate_manifest({"connector_key": "mock.local.preview"})
    client.connector_runtime.egress_preview({"connector_key": "mock.local.preview"})
    client.connector_runtime.ingress_preview({"connector_key": "mock.local.preview"})
    client.connector_runtime.audit({"owner_scope": ["workspace:main"]})

    assert seen == [
        ("GET", "/brain/connector-runtime/status"),
        ("POST", "/brain/connector-runtime/mock-manifest/validate"),
        ("POST", "/brain/connector-runtime/egress-preview"),
        ("POST", "/brain/connector-runtime/ingress-preview"),
        ("POST", "/brain/connector-runtime/audit"),
    ]


def test_connector_runtime_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.connector_runtime as resource

    assert "aion_brain" not in resource.__dict__
