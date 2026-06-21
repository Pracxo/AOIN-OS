from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_prompts_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.prompts.compile({"owner_scope": ["workspace:main"]})
    client.prompts.preview({"prompt_packet_id": "packet-1", "owner_scope": ["workspace:main"]})
    client.prompts.list_packets(["workspace:main"])
    client.prompts.boundary_check("packet-1", ["workspace:main"])
    client.prompts.injection_findings(trace_id="trace-1")
    client.prompts.list_manifests(["workspace:main"])
    client.prompts.seed_templates(["workspace:main"])

    assert seen == [
        ("POST", "/brain/prompts/compile"),
        ("POST", "/brain/prompts/preview"),
        ("GET", "/brain/prompts/packets"),
        ("POST", "/brain/prompts/boundary-check"),
        ("GET", "/brain/prompts/injection-findings"),
        ("GET", "/brain/prompts/model-input-manifests"),
        ("POST", "/brain/prompts/templates/seed-defaults"),
    ]


def test_prompts_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.prompts as prompts_resource

    assert "aion_brain" not in prompts_resource.__dict__
