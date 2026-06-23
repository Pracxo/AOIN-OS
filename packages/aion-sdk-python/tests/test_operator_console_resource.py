from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_operator_console_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.operator_console.list_views(["workspace:main"])
    client.operator_console.view_model({"view": "overview", "owner_scope": ["workspace:main"]})
    client.operator_console.audit({"owner_scope": ["workspace:main"]})
    client.operator_console.workflows(["workspace:main"])
    client.operator_console.demo_map(["workspace:main"])

    assert seen == [
        ("GET", "/brain/operator-console/views"),
        ("POST", "/brain/operator-console/view-model"),
        ("POST", "/brain/operator-console/audit"),
        ("GET", "/brain/operator-console/workflows"),
        ("GET", "/brain/operator-console/demo-map"),
    ]
