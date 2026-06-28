from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_auth_runtime_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.auth_runtime.status(["workspace:main"])
    client.auth_runtime.mock_claims_preview({"subject": "local.operator", "roles": ["operator"]})
    client.auth_runtime.audit({"owner_scope": ["workspace:main"]})

    assert seen == [
        ("GET", "/brain/auth-runtime/status"),
        ("POST", "/brain/auth-runtime/mock-claims/preview"),
        ("POST", "/brain/auth-runtime/audit"),
    ]


def test_auth_runtime_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.auth_runtime as resource

    assert "aion_brain" not in resource.__dict__
