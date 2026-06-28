from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_action_authorization_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.action_authorization.authorize({"action_key": "operator.review"})
    client.action_authorization.audit({"owner_scope": ["workspace:main"]})
    client.action_authorization.status(["workspace:main"])

    assert seen == [
        ("POST", "/brain/action-authorization/authorize"),
        ("POST", "/brain/action-authorization/audit"),
        ("GET", "/brain/action-authorization/status"),
    ]


def test_action_authorization_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.action_authorization as resource

    assert "aion_brain" not in resource.__dict__
