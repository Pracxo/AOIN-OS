from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_explanations_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.explanations.explain({"target_type": "trace", "owner_scope": ["workspace:main"]})
    client.explanations.get("explanation-1", ["workspace:main"])
    client.explanations.verify("explanation-1")
    client.explanations.why_not(
        {
            "question": "Why did this not continue?",
            "target_type": "trace",
            "owner_scope": ["workspace:main"],
        }
    )
    client.explanations.trace_narrative(
        "trace-1",
        {"trace_id": "trace-1", "owner_scope": ["workspace:main"]},
    )
    client.explanations.feedback(
        {
            "explanation_feedback_id": "feedback-1",
            "explanation_id": "explanation-1",
            "feedback_type": "helpful",
        }
    )

    assert seen == [
        ("POST", "/brain/explanations"),
        ("GET", "/brain/explanations/explanation-1"),
        ("POST", "/brain/explanations/explanation-1/verify"),
        ("POST", "/brain/explanations/why-not"),
        ("POST", "/brain/traces/trace-1/narrative"),
        ("POST", "/brain/explanations/feedback"),
    ]


def test_explanations_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.explanations as explanations_resource

    assert "aion_brain" not in explanations_resource.__dict__
