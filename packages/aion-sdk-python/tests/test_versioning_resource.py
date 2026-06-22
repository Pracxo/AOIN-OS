from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_versioning_resource_create_manifest_calls_public_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"version": "0.1.0"})

    _client(handler).versioning.create_manifest(
        {"version": "0.1.0", "owner_scope": ["workspace:main"]}
    )

    assert seen == {"method": "POST", "path": "/brain/versioning/manifests"}


def test_versioning_resource_sdk_compatibility_uses_query_scope() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["scope"] = request.url.params.get("scope", "")
        return httpx.Response(200, json={"compatible": True})

    _client(handler).versioning.sdk_compatibility(["workspace:main"])

    assert seen["path"] == "/brain/versioning/sdk-compatibility"
    assert seen["scope"] == "workspace:main"


def test_versioning_resource_freeze_gate_calls_public_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"status": "passed"})

    _client(handler).versioning.run_freeze_gate(
        {"version": "0.1.0", "owner_scope": ["workspace:main"]}
    )

    assert seen["path"] == "/brain/freeze-gate/run"
