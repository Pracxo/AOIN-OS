from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_action_proposals_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.action_proposals.create({"source_type": "generic", "owner_scope": ["workspace:main"]})
    client.action_proposals.get("proposal-1", ["workspace:main"])
    client.action_proposals.query({"scope": ["workspace:main"]})
    client.action_proposals.archive("proposal-1", "done")
    client.action_proposals.delete("proposal-1", "remove")
    client.action_proposals.review_tool_intent("tool-1", {"owner_scope": ["workspace:main"]})
    client.action_proposals.list_tool_intent_reviews(tool_intent_id="tool-1")
    client.action_proposals.review("proposal-1", {"decision": "approve_for_handoff"})
    client.action_proposals.list_reviews("proposal-1")
    client.action_proposals.list_blockers(action_proposal_id="proposal-1")
    client.action_proposals.resolve_blocker("blocker-1", "resolved")
    client.action_proposals.handoff({"action_proposal_id": "proposal-1", "target_system": "noop"})
    client.action_proposals.get_handoff("handoff-1", ["workspace:main"])
    client.action_proposals.list_handoffs(action_proposal_id="proposal-1")

    assert seen == [
        ("POST", "/brain/action-proposals"),
        ("GET", "/brain/action-proposals/proposal-1"),
        ("POST", "/brain/action-proposals/query"),
        ("POST", "/brain/action-proposals/proposal-1/archive"),
        ("DELETE", "/brain/action-proposals/proposal-1"),
        ("POST", "/brain/action-proposals/tool-intents/tool-1/review"),
        ("GET", "/brain/action-proposals/tool-intent-reviews"),
        ("POST", "/brain/action-proposals/proposal-1/review"),
        ("GET", "/brain/action-proposals/proposal-1/reviews"),
        ("GET", "/brain/action-proposals/blockers"),
        ("POST", "/brain/action-proposals/blockers/blocker-1/resolve"),
        ("POST", "/brain/action-proposals/handoff"),
        ("GET", "/brain/action-proposals/handoffs/handoff-1"),
        ("GET", "/brain/action-proposals/handoffs"),
    ]


def test_action_proposals_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.action_proposals as resource

    assert "aion_brain" not in resource.__dict__
