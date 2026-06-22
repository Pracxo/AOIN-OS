from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_learning_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.learning.create_experience({"source_type": "generic"})
    client.learning.get_experience("experience-1", ["workspace:main"])
    client.learning.query({"scope": ["workspace:main"]})
    client.learning.archive_experience("experience-1", "reviewed")
    client.learning.mine_patterns({"owner_scope": ["workspace:main"]})
    client.learning.list_patterns(scope=["workspace:main"])
    client.learning.list_lessons(scope=["workspace:main"])
    client.learning.synthesize({"owner_scope": ["workspace:main"]})
    client.learning.get_synthesis("synthesis-1")
    client.learning.list_skill_suggestions(scope=["workspace:main"])
    client.learning.accept_skill_suggestion("suggestion-1", "reviewed")
    client.learning.reject_skill_suggestion("suggestion-1", "superseded")
    client.learning.convert_skill_suggestion("suggestion-1", reason="candidate only")
    client.learning.list_regression_suggestions(scope=["workspace:main"])
    client.learning.accept_regression_suggestion("regression-1", "reviewed")
    client.learning.reject_regression_suggestion("regression-1", "superseded")

    assert seen == [
        ("POST", "/brain/learning/experiences"),
        ("GET", "/brain/learning/experiences/experience-1"),
        ("POST", "/brain/learning/query"),
        ("POST", "/brain/learning/experiences/experience-1/archive"),
        ("POST", "/brain/learning/patterns/mine"),
        ("GET", "/brain/learning/patterns"),
        ("GET", "/brain/learning/lessons"),
        ("POST", "/brain/learning/synthesize"),
        ("GET", "/brain/learning/synthesis/synthesis-1"),
        ("GET", "/brain/learning/skill-suggestions"),
        ("POST", "/brain/learning/skill-suggestions/suggestion-1/accept"),
        ("POST", "/brain/learning/skill-suggestions/suggestion-1/reject"),
        ("POST", "/brain/learning/skill-suggestions/suggestion-1/convert-to-candidate"),
        ("GET", "/brain/learning/regression-suggestions"),
        ("POST", "/brain/learning/regression-suggestions/regression-1/accept"),
        ("POST", "/brain/learning/regression-suggestions/regression-1/reject"),
    ]
