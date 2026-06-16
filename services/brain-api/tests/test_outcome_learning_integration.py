from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_outcome_learning_bridge_can_create_experience() -> None:
    client = TestClient(create_app(kernel_container()))
    outcome = client.post(
        "/brain/outcomes",
        json={
            "source_type": "generic",
            "source_id": "source-1",
            "outcome_type": "generic",
            "title": "Generic outcome",
            "summary": "Generic outcome for learning.",
            "owner_scope": ["workspace:main"],
            "score": 0.2,
            "confidence": 0.8,
        },
    )
    assert outcome.status_code == 200
    outcome_id = outcome.json()["outcome_id"]

    bridge = client.post(
        f"/brain/outcomes/{outcome_id}/learning-bridge",
        json={"dry_run": False},
    )
    assert bridge.status_code == 200
    assert bridge.json()["experience_id"]

    query = client.post(
        "/brain/learning/query",
        json={"scope": ["workspace:main"], "source_types": ["outcome"]},
    )
    assert query.status_code == 200
    assert query.json()["experiences"][0]["source_id"] == outcome_id
