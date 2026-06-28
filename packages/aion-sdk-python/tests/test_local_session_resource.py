from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_local_session_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.local_session.preview({"roles": ["operator"], "owner_scope": scope})
    client.local_session.context({"roles": ["operator"], "owner_scope": scope})
    client.local_session.status(scope)
    client.local_session.boundary_check(scope)
    client.local_session.audit({"owner_scope": scope})

    assert seen == [
        ("POST", "/brain/local-session/preview"),
        ("POST", "/brain/local-session/context"),
        ("GET", "/brain/local-session/status"),
        ("POST", "/brain/local-session/boundary-check"),
        ("POST", "/brain/local-session/audit"),
    ]


def test_local_session_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.local_session as resource

    assert "aion_brain" not in resource.__dict__
