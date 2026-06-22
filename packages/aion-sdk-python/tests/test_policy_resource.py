from __future__ import annotations

import json
from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_policy_resource_seed_defaults_calls_catalog_endpoints() -> None:
    calls: list[tuple[str, str, dict[str, object]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.policy.seed_actions(dry_run=True)
    client.policy.seed_roles(dry_run=False)

    assert calls == [
        ("POST", "/brain/policy-catalog/seed-defaults", {"dry_run": True}),
        ("POST", "/brain/policy-catalog/roles/seed-defaults", {"dry_run": False}),
    ]


def test_policy_resource_bundle_export_uses_public_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"policy_bundle_id": "bundle-1"})

    result = _client(handler).policy.export_bundle({"bundle_type": "full"})

    assert result == {"policy_bundle_id": "bundle-1"}
    assert seen == {
        "method": "POST",
        "path": "/brain/policy/bundles/export",
        "payload": {"bundle_type": "full"},
    }
