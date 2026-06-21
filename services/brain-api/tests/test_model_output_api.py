"""Model output API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_model_output_api_receive_govern_and_query() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/model-outputs",
        json={
            "trace_id": "trace-1",
            "output_type": "mixed",
            "raw_output": 'Answer safely.\ntool: echo {"value":"ok"}',
            "owner_scope": ["workspace:main"],
        },
    )
    assert created.status_code == 200
    output_id = created.json()["model_output_id"]
    assert "raw_output" not in created.json()

    governed = client.post(
        f"/brain/model-outputs/{output_id}/govern",
        json={
            "trace_id": "trace-1",
            "model_output_id": output_id,
            "owner_scope": ["workspace:main"],
        },
    )
    queried = client.post(
        "/brain/model-outputs/query",
        json={"scope": ["workspace:main"], "trace_id": "trace-1"},
    )
    segments = client.get(
        f"/brain/model-outputs/{output_id}/segments",
        params={"scope": "workspace:main"},
    )
    candidates = client.get(
        "/brain/model-outputs/response-candidates",
        params={"scope": "workspace:main"},
    )
    intents = client.get(
        "/brain/model-outputs/tool-intents",
        params={"scope": "workspace:main"},
    )

    assert governed.status_code == 200
    assert governed.json()["blocked"] is True
    assert queried.status_code == 200
    assert queried.json()["total_count"] == 1
    assert segments.status_code == 200
    assert candidates.status_code == 200
    assert intents.status_code == 200
    assert intents.json()[0]["status"] == "blocked"


def test_model_output_api_rejects_missing_required_fields() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post("/brain/model-outputs", json={"owner_scope": ["workspace:main"]})

    assert response.status_code == 422


def test_model_output_api_validate_structured() -> None:
    client = TestClient(create_app(kernel_container()))
    created = client.post(
        "/brain/model-outputs",
        json={
            "trace_id": "trace-json",
            "output_type": "json",
            "raw_output": '{"content":"ok"}',
            "owner_scope": ["workspace:main"],
        },
    )
    output_id = created.json()["model_output_id"]

    validated = client.post(
        f"/brain/model-outputs/{output_id}/validate-structured",
        json={"schema_name": "response_candidate"},
        params={"scope": "workspace:main"},
    )

    assert validated.status_code == 200
    assert validated.json()["valid"] is True
