from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_dialogue_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.dialogue.turn({"message": "hello", "owner_scope": ["workspace:main"]})
    client.dialogue.create_session({"title": "Session", "owner_scope": ["workspace:main"]})
    client.dialogue.answer_clarification("clarification-1", "answer")

    assert seen == [
        ("POST", "/brain/dialogue/turn"),
        ("POST", "/brain/dialogue/sessions"),
        ("POST", "/brain/dialogue/clarifications/clarification-1/answer"),
    ]


def test_dialogue_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.dialogue as dialogue_resource

    assert "aion_brain" not in dialogue_resource.__dict__
