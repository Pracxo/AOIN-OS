from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_outcomes_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.outcomes.create({"source_type": "command"})
    client.outcomes.get("outcome-1", ["workspace:main"])
    client.outcomes.query({"scope": ["workspace:main"]})
    client.outcomes.close("outcome-1", "done", ["workspace:main"])
    client.outcomes.create_expected_effect({"source_type": "command"})
    client.outcomes.list_expected_effects(source_type="command")
    client.outcomes.create_observed_effect({"source_type": "command"})
    client.outcomes.list_observed_effects(source_type="command")
    client.outcomes.verify({"source_id": "command-1"})
    client.outcomes.get_verification("verification-1")
    client.outcomes.create_attribution({"causal_attribution_id": "cause-1"})
    client.outcomes.list_attributions(outcome_id="outcome-1")
    client.outcomes.create_feedback({"outcome_feedback_id": "feedback-1"})
    client.outcomes.list_feedback(status="open")
    client.outcomes.resolve_feedback("feedback-1", "done")
    client.outcomes.learning_bridge("outcome-1")

    assert seen == [
        ("POST", "/brain/outcomes"),
        ("GET", "/brain/outcomes/outcome-1"),
        ("POST", "/brain/outcomes/query"),
        ("POST", "/brain/outcomes/outcome-1/close"),
        ("POST", "/brain/outcomes/expected-effects"),
        ("GET", "/brain/outcomes/expected-effects"),
        ("POST", "/brain/outcomes/observed-effects"),
        ("GET", "/brain/outcomes/observed-effects"),
        ("POST", "/brain/outcomes/verify"),
        ("GET", "/brain/outcomes/verifications/verification-1"),
        ("POST", "/brain/outcomes/attributions"),
        ("GET", "/brain/outcomes/attributions"),
        ("POST", "/brain/outcomes/feedback"),
        ("GET", "/brain/outcomes/feedback"),
        ("POST", "/brain/outcomes/feedback/feedback-1/resolve"),
        ("POST", "/brain/outcomes/outcome-1/learning-bridge"),
    ]
