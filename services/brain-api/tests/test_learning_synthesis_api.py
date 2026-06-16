from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_learning_synthesis_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))

    first = _create_experience(client, "source-1")
    second = _create_experience(client, "source-2")

    assert (
        client.get(
            f"/brain/learning/experiences/{first}",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/brain/learning/query",
            json={"scope": ["workspace:main"], "query": "generic"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/learning/experiences/{second}/archive",
            json={"reason": "reviewed"},
        ).status_code
        == 200
    )

    mine = client.post(
        "/brain/learning/patterns/mine",
        json={
            "owner_scope": ["workspace:main"],
            "experience_ids": [first, second],
            "dry_run": False,
        },
    )
    assert mine.status_code == 200
    pattern_id = mine.json()["patterns"][0]["pattern_id"]
    assert (
        client.get(
            "/brain/learning/patterns",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )

    synthesis = client.post(
        "/brain/learning/synthesize",
        json={
            "mode": "controlled",
            "owner_scope": ["workspace:main"],
            "pattern_ids": [pattern_id],
            "create_skill_suggestions": True,
            "create_regression_suggestions": True,
        },
    )
    assert synthesis.status_code == 200
    body = synthesis.json()
    run_id = body["synthesis_run_id"]
    skill_id = body["skill_candidate_suggestions"][0]["suggestion_id"]
    regression_id = body["regression_candidate_suggestions"][0]["regression_suggestion_id"]

    assert client.get(f"/brain/learning/synthesis/{run_id}").status_code == 200
    assert (
        client.get(
            "/brain/learning/lessons",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/brain/learning/skill-suggestions",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/learning/skill-suggestions/{skill_id}/accept",
            json={"reason": "reviewed"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/learning/skill-suggestions/{skill_id}/convert-to-candidate",
            json={"reason": "candidate only", "approval_present": True},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/brain/learning/regression-suggestions",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/learning/regression-suggestions/{regression_id}/accept",
            json={"reason": "reviewed"},
        ).status_code
        == 200
    )


def _create_experience(client: TestClient, source_id: str) -> str:
    response = client.post(
        "/brain/learning/experiences",
        json={
            "source_type": "generic",
            "source_id": source_id,
            "experience_type": "failure",
            "title": f"Experience {source_id}",
            "summary": "Generic repeated failure",
            "owner_scope": ["workspace:main"],
            "score": 0.2,
            "confidence": 0.8,
        },
    )
    assert response.status_code == 200
    return str(response.json()["experience_id"])
