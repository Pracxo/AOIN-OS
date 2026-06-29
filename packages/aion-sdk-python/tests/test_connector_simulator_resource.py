from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_connector_simulator_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.connector_simulator.simulate({"connector_key": "mock.local.preview"})
    client.connector_simulator.replay({"connector_key": "mock.local.preview"})
    client.connector_simulator.policy_readiness({"connector_key": "mock.local.preview"})
    client.connector_simulator.status(["workspace:main"])
    client.connector_simulator.query({"connector_key": "mock.local.preview"})

    assert seen == [
        ("POST", "/brain/connector-simulator/simulate"),
        ("POST", "/brain/connector-simulator/replay"),
        ("POST", "/brain/connector-simulator/policy-readiness"),
        ("GET", "/brain/connector-simulator/status"),
        ("POST", "/brain/connector-simulator/query"),
    ]


def test_connector_simulator_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.connector_simulator as resource

    assert "aion_brain" not in resource.__dict__
