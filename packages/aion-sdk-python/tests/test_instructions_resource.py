from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_instructions_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.instructions.create_instruction({"instruction_text": "Keep it concise."})
    client.instructions.resolve({"owner_scope": ["workspace:main"]})
    client.instructions.confirm_preference("preference-1", "explicit")
    client.instructions.effective_style(["workspace:main"])

    assert seen == [
        ("POST", "/brain/instructions"),
        ("POST", "/brain/instructions/resolve"),
        ("POST", "/brain/preferences/preference-1/confirm"),
        ("GET", "/brain/style-profiles/effective"),
    ]


def test_instructions_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.instructions as instructions_resource

    assert "aion_brain" not in instructions_resource.__dict__
