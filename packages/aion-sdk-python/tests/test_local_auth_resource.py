from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_local_auth_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.local_auth.roles(scope)
    client.local_auth.simulate({"roles": ["operator"], "owner_scope": scope})
    client.local_auth.filter_console({"view_model": {}, "auth_context": {}})
    client.local_auth.role_matrix(scope)
    client.local_auth.role_access_audit({"owner_scope": scope})
    client.local_auth.audit({"owner_scope": scope})
    client.local_auth.status(scope)

    assert seen == [
        ("GET", "/brain/local-auth/roles"),
        ("POST", "/brain/local-auth/simulate"),
        ("POST", "/brain/local-auth/filter-console"),
        ("GET", "/brain/local-auth/role-matrix"),
        ("POST", "/brain/local-auth/role-access-audit"),
        ("POST", "/brain/local-auth/audit"),
        ("GET", "/brain/local-auth/status"),
    ]


def test_local_auth_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.local_auth as resource

    assert "aion_brain" not in resource.__dict__
