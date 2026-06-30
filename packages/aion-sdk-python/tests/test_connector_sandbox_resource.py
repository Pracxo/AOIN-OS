from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_connector_sandbox_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.connector_sandbox.boundary()
    client.connector_sandbox.capability_rules()
    client.connector_sandbox.readiness({"connector_key": "mock.local.preview"})
    client.connector_sandbox.query({"connector_key": "mock.local.preview"})
    client.connector_sandbox.status(["workspace:main"])

    assert seen == [
        ("GET", "/brain/connector-sandbox/boundary"),
        ("GET", "/brain/connector-sandbox/capability-rules"),
        ("POST", "/brain/connector-sandbox/readiness"),
        ("POST", "/brain/connector-sandbox/query"),
        ("GET", "/brain/connector-sandbox/status"),
    ]


def test_connector_sandbox_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.connector_sandbox as resource

    assert "aion_brain" not in resource.__dict__
