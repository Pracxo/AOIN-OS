from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_self_model_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    describe = client.get("/brain/self", params={"scope": "workspace:main"})
    assert describe.status_code == 200
    assert describe.json()["full_name"] == "Adaptive Intelligence Orchestration Nexus"

    capabilities = client.get("/brain/self/capabilities", params={"scope": "workspace:main"})
    assert capabilities.status_code == 200
    assert any(item["capability_key"] == "aion.optional.turbovec" for item in capabilities.json())

    refresh = client.post(
        "/brain/self/capabilities/refresh",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    assert refresh.status_code == 200

    seed = client.post(
        "/brain/self/limitations/seed-defaults",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    assert seed.status_code == 200
    assert seed.json()["created_count"] == 0

    created = client.post(
        "/brain/self/limitations",
        json={
            "limitation_key": "generic.api_limit",
            "category": "generic",
            "severity": "high",
            "title": "Generic API limitation",
            "description": "A generic API limitation.",
            "owner_scope": ["workspace:main"],
        },
    )
    assert created.status_code == 200
    limitation_id = created.json()["limitation_id"]

    listed = client.get("/brain/self/limitations", params={"scope": "workspace:main"})
    assert listed.status_code == 200
    assert any(item["limitation_id"] == limitation_id for item in listed.json())

    resolved = client.post(
        f"/brain/self/limitations/{limitation_id}/resolve",
        json={"reason": "Reviewed."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    confidence = client.post(
        "/brain/self/confidence/calibrate",
        json={
            "source_type": "response",
            "source_id": "response-1",
            "evidence_refs": ["evidence-1"],
        },
    )
    assert confidence.status_code == 200
    assert confidence.json()["confidence_level"] in {"medium", "high"}

    confidence_list = client.get("/brain/self/confidence", params={"limit": 10})
    assert confidence_list.status_code == 200

    assessment = client.post(
        "/brain/self/assessment/run",
        json={"owner_scope": ["workspace:main"], "assessment_type": "full"},
    )
    assert assessment.status_code == 200
    assessment_id = assessment.json()["self_assessment_id"]

    get_assessment = client.get(f"/brain/self/assessment/{assessment_id}")
    assert get_assessment.status_code == 200

    introspection = client.post(
        "/brain/self/introspection",
        json={"owner_scope": ["workspace:main"], "snapshot_type": "manual"},
    )
    assert introspection.status_code == 200
    snapshot_id = introspection.json()["introspection_snapshot_id"]

    get_snapshot = client.get(
        f"/brain/self/introspection/{snapshot_id}",
        params={"scope": "workspace:main"},
    )
    assert get_snapshot.status_code == 200

    snapshots = client.get("/brain/self/introspection", params={"scope": "workspace:main"})
    assert snapshots.status_code == 200
