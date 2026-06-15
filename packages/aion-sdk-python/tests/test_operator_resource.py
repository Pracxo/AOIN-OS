from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_operator_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.operator.overview({"owner_scope": ["workspace:main"]})
    client.operator.readiness(["workspace:main"])
    client.operator.actions(["workspace:main"])
    client.operator.acknowledge(
        {"source_type": "generic", "source_id": "item-1", "reason": "seen"}
    )

    assert seen == [
        ("POST", "/brain/operator/overview"),
        ("GET", "/brain/operator/readiness"),
        ("GET", "/brain/operator/actions"),
        ("POST", "/brain/operator/actions/acknowledge"),
    ]


def test_operator_resource_snapshot_and_runbook_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.operator.create_snapshot({"owner_scope": ["workspace:main"]})
    client.operator.get_snapshot("snapshot-1", ["workspace:main"])
    client.operator.list_snapshots(["workspace:main"])
    client.operator.runbooks()

    assert seen == [
        ("POST", "/brain/operator/snapshots"),
        ("GET", "/brain/operator/snapshots/snapshot-1"),
        ("GET", "/brain/operator/snapshots"),
        ("GET", "/brain/operator/runbooks"),
    ]
