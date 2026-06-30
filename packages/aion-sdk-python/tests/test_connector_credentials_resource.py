from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_connector_credentials_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.connector_credentials.boundary()
    client.connector_credentials.lifecycle()
    client.connector_credentials.authorization()
    client.connector_credentials.readiness({"connector_key": "mock.local.preview"})
    client.connector_credentials.redaction_preview({"sample": "placeholder"})
    client.connector_credentials.query({"connector_key": "mock.local.preview"})
    client.connector_credentials.status(["workspace:main"])

    assert seen == [
        ("GET", "/brain/connector-credentials/boundary"),
        ("GET", "/brain/connector-credentials/lifecycle"),
        ("GET", "/brain/connector-credentials/authorization"),
        ("POST", "/brain/connector-credentials/readiness"),
        ("POST", "/brain/connector-credentials/redaction-preview"),
        ("POST", "/brain/connector-credentials/query"),
        ("GET", "/brain/connector-credentials/status"),
    ]


def test_connector_credentials_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.connector_credentials as resource

    assert "aion_brain" not in resource.__dict__
