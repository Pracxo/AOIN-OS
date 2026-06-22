from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_grounding_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.grounding.verify({"target_type": "generic", "owner_scope": ["workspace:main"]})
    client.grounding.map_response("response-1", ["workspace:main"])
    client.grounding.coverage({"response_id": "response-1", "owner_scope": ["workspace:main"]})
    client.grounding.query({"scope": ["workspace:main"]})
    client.grounding.unsupported(response_id="response-1")

    assert seen == [
        ("POST", "/brain/grounding/verify"),
        ("POST", "/brain/grounding/map-response/response-1"),
        ("POST", "/brain/grounding/coverage"),
        ("POST", "/brain/grounding/query"),
        ("GET", "/brain/grounding/unsupported"),
    ]


def test_grounding_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.grounding as grounding_resource

    assert "aion_brain" not in grounding_resource.__dict__
