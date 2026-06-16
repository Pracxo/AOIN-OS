from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_responses_resource_verify_calls_expected_endpoint() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.responses.verify("response-1")
    client.responses.get("response-1")

    assert seen == [
        ("POST", "/brain/responses/response-1/verify"),
        ("GET", "/brain/responses/response-1"),
    ]


def test_responses_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.responses as responses_resource

    assert "aion_brain" not in responses_resource.__dict__
