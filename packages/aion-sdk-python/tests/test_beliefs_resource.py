from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_beliefs_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.beliefs.create_claim({"claim_text": "A claim", "owner_scope": ["workspace:main"]})
    client.beliefs.query({"scope": ["workspace:main"]})
    client.beliefs.run_truth_maintenance({"owner_scope": ["workspace:main"]})

    assert seen == [
        ("POST", "/brain/beliefs/claims"),
        ("POST", "/brain/beliefs/query"),
        ("POST", "/brain/beliefs/truth-maintenance/run"),
    ]


def test_beliefs_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.beliefs as beliefs_resource

    assert "aion_brain" not in beliefs_resource.__dict__
