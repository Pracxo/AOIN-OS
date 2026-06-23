from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_operator_actions_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.operator_actions.create_request({"action_key": "operator.review"})
    client.operator_actions.get_request("request-1", ["workspace:main"])
    client.operator_actions.list_requests(["workspace:main"])
    client.operator_actions.create_preview("request-1", ["workspace:main"])
    client.operator_actions.previews(["workspace:main"])
    client.operator_actions.blockers(["workspace:main"], operator_action_request_id="request-1")
    client.operator_actions.dismiss_blocker("blocker-1", "reviewed")
    client.operator_actions.review("request-1", {"decision": "approve_preview_only"})
    client.operator_actions.reviews(["workspace:main"], operator_action_request_id="request-1")
    client.operator_actions.query({"scope": ["workspace:main"]})

    assert seen == [
        ("POST", "/brain/operator-actions/requests"),
        ("GET", "/brain/operator-actions/requests/request-1"),
        ("GET", "/brain/operator-actions/requests"),
        ("POST", "/brain/operator-actions/requests/request-1/preview"),
        ("GET", "/brain/operator-actions/previews"),
        ("GET", "/brain/operator-actions/blockers"),
        ("POST", "/brain/operator-actions/blockers/blocker-1/dismiss"),
        ("POST", "/brain/operator-actions/requests/request-1/review"),
        ("GET", "/brain/operator-actions/reviews"),
        ("POST", "/brain/operator-actions/query"),
    ]


def test_operator_actions_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.operator_actions as resource

    assert "aion_brain" not in resource.__dict__
