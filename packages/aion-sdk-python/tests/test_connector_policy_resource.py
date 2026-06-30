from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_connector_policy_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.connector_policy.catalog()
    client.connector_policy.matrix()
    client.connector_policy.dry_run({"connector_key": "mock.local.preview"})
    client.connector_policy.query_traceability({"connector_key": "mock.local.preview"})
    client.connector_policy.status(["workspace:main"])

    assert seen == [
        ("GET", "/brain/connector-policy/catalog"),
        ("GET", "/brain/connector-policy/matrix"),
        ("POST", "/brain/connector-policy/dry-run"),
        ("POST", "/brain/connector-policy/traceability/query"),
        ("GET", "/brain/connector-policy/status"),
    ]


def test_connector_policy_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.connector_policy as resource

    assert "aion_brain" not in resource.__dict__

