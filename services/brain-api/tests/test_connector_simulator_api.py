from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_connector_simulator_api_endpoints_are_synthetic_only() -> None:
    client = TestClient(create_app(kernel_container()))

    simulate = client.post(
        "/brain/connector-simulator/simulate",
        json={
            "connector_key": "mock.local.preview",
            "owner_scope": ["workspace:main"],
            "request_shape": {"object": "synthetic_request"},
            "expected_response_shape": {"object": "synthetic_response"},
        },
    )
    replay = client.post(
        "/brain/connector-simulator/replay",
        json={
            "replay_fixture_id": "fixture-1",
            "connector_key": "mock.local.preview",
            "name": "Local Replay",
            "description": "Synthetic replay fixture.",
            "owner_scope": ["workspace:main"],
            "fixture_type": "synthetic_replay",
            "request_shape": {"object": "synthetic_request"},
            "response_shape": {"object": "synthetic_response"},
            "synthetic": True,
            "trusted": False,
        },
    )
    readiness = client.post(
        "/brain/connector-simulator/policy-readiness",
        json={
            "connector_key": "mock.local.preview",
            "owner_scope": ["workspace:main"],
            "declared_policy_actions": [
                "connector_simulator.simulate",
                "connector_simulator.replay",
                "connector_simulator.policy_readiness",
            ],
        },
    )
    status = client.get("/brain/connector-simulator/status", params={"scope": "workspace:main"})
    query = client.post(
        "/brain/connector-simulator/query",
        json={"connector_key": "mock.local.preview", "owner_scope": ["workspace:main"]},
    )

    assert simulate.status_code == 200
    assert simulate.json()["synthetic"] is True
    assert simulate.json()["trusted"] is False
    assert simulate.json()["external_calls_made"] is False
    assert replay.status_code == 200
    assert replay.json()["metadata"]["replay_fixture_id"] == "fixture-1"
    assert readiness.status_code == 200
    assert readiness.json()["external_calls_allowed"] is False
    assert status.status_code == 200
    assert status.json()["connector_runtime_enabled"] is False
    assert query.status_code == 200
    assert query.json()["read_only"] is True
