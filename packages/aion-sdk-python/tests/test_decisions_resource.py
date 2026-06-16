from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_decisions_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.decisions.create_frame({"title": "Choose", "question": "Which?"})
    client.decisions.get_frame("frame-1", ["workspace:main"])
    client.decisions.list_frames(["workspace:main"])
    client.decisions.close_frame("frame-1", "done", ["workspace:main"])
    client.decisions.create_option({"decision_frame_id": "frame-1"})
    client.decisions.list_options("frame-1")
    client.decisions.seed_utility_profiles(["workspace:main"])
    client.decisions.list_utility_profiles(["workspace:main"])
    client.decisions.evaluate({"decision_frame_id": "frame-1"})
    client.decisions.recommend("frame-1", {"dry_run": True})
    client.decisions.run_counterfactual({"decision_frame_id": "frame-1"})
    client.decisions.get_counterfactual("counterfactual-1")
    client.decisions.record_decision({"decision_frame_id": "frame-1", "rationale": "only"})
    client.decisions.get_decision_record("record-1", ["workspace:main"])
    client.decisions.list_decision_records(["workspace:main"])

    assert seen == [
        ("POST", "/brain/decisions/frames"),
        ("GET", "/brain/decisions/frames/frame-1"),
        ("GET", "/brain/decisions/frames"),
        ("POST", "/brain/decisions/frames/frame-1/close"),
        ("POST", "/brain/decisions/options"),
        ("GET", "/brain/decisions/frames/frame-1/options"),
        ("POST", "/brain/decisions/utility-profiles/seed-defaults"),
        ("GET", "/brain/decisions/utility-profiles"),
        ("POST", "/brain/decisions/evaluate"),
        ("POST", "/brain/decisions/recommend/frame-1"),
        ("POST", "/brain/decisions/counterfactuals/run"),
        ("GET", "/brain/decisions/counterfactuals/counterfactual-1"),
        ("POST", "/brain/decisions/journal"),
        ("GET", "/brain/decisions/journal/record-1"),
        ("GET", "/brain/decisions/journal"),
    ]
