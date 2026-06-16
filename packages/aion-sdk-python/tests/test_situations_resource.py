from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_situations_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.situations.create(
        {"title": "Current", "summary": "State", "owner_scope": ["workspace:main"]}
    )
    client.situations.get("situation-1", ["workspace:main"])
    client.situations.query({"scope": ["workspace:main"]})
    client.situations.close("situation-1", "done", ["workspace:main"])
    client.situations.create_atom(
        {"source_id": "source-1", "predicate": "status", "owner_scope": ["workspace:main"]}
    )
    client.situations.get_atom("atom-1", ["workspace:main"])
    client.situations.list_atoms(["workspace:main"])
    client.situations.project({"mode": "dry_run", "owner_scope": ["workspace:main"]})
    client.situations.get_projection_run("run-1")
    client.situations.list_transitions()
    client.situations.create_temporal_window({"owner_scope": ["workspace:main"]})
    client.situations.get_temporal_window("window-1", ["workspace:main"])
    client.situations.list_temporal_windows(["workspace:main"])
    client.situations.record_continuity({"owner_scope": ["workspace:main"]})
    client.situations.list_continuity(["workspace:main"])

    assert seen == [
        ("POST", "/brain/situations"),
        ("GET", "/brain/situations/situation-1"),
        ("POST", "/brain/situations/query"),
        ("POST", "/brain/situations/situation-1/close"),
        ("POST", "/brain/situations/state-atoms"),
        ("GET", "/brain/situations/state-atoms/atom-1"),
        ("GET", "/brain/situations/state-atoms"),
        ("POST", "/brain/situations/project"),
        ("GET", "/brain/situations/projection-runs/run-1"),
        ("GET", "/brain/situations/transitions"),
        ("POST", "/brain/situations/temporal-windows"),
        ("GET", "/brain/situations/temporal-windows/window-1"),
        ("GET", "/brain/situations/temporal-windows"),
        ("POST", "/brain/situations/continuity"),
        ("GET", "/brain/situations/continuity"),
    ]
