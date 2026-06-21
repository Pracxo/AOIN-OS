from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_model_outputs_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.model_outputs.create({"raw_output": "ok", "owner_scope": ["workspace:main"]})
    client.model_outputs.get("output-1", ["workspace:main"])
    client.model_outputs.query({"scope": ["workspace:main"]})
    client.model_outputs.govern("output-1", {"owner_scope": ["workspace:main"]})
    client.model_outputs.segments("output-1", ["workspace:main"])
    client.model_outputs.validate_structured("output-1", ["workspace:main"])
    client.model_outputs.response_candidates(["workspace:main"])
    client.model_outputs.promote_candidate("candidate-1")
    client.model_outputs.tool_intents(["workspace:main"])
    client.model_outputs.reject_tool_intent("tool-intent-1", "not needed")

    assert seen == [
        ("POST", "/brain/model-outputs"),
        ("GET", "/brain/model-outputs/output-1"),
        ("POST", "/brain/model-outputs/query"),
        ("POST", "/brain/model-outputs/output-1/govern"),
        ("GET", "/brain/model-outputs/output-1/segments"),
        ("POST", "/brain/model-outputs/output-1/validate-structured"),
        ("GET", "/brain/model-outputs/response-candidates"),
        ("POST", "/brain/model-outputs/response-candidates/candidate-1/promote"),
        ("GET", "/brain/model-outputs/tool-intents"),
        ("POST", "/brain/model-outputs/tool-intents/tool-intent-1/reject"),
    ]


def test_model_outputs_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.model_outputs as resource

    assert "aion_brain" not in resource.__dict__
