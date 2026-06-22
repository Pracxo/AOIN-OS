"""Release candidate API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_release_candidate_api_routes_work_without_external_services() -> None:
    client = TestClient(create_app(kernel_container()))

    candidate = client.post(
        "/brain/rc/candidates",
        json={
            "rc_key": "rc.api",
            "version": "0.1.0",
            "owner_scope": ["workspace:main"],
        },
    )
    candidate_id = candidate.json()["release_candidate_id"]
    matrix = client.post(
        "/brain/rc/matrices",
        json={
            "matrix_key": "rc.api",
            "version": "0.1.0",
            "owner_scope": ["workspace:main"],
            "required_checks": ["tests.brain"],
            "optional_checks": [],
        },
    )
    matrix_id = matrix.json()["verification_matrix_id"]
    run = client.post(
        "/brain/rc/gate/run",
        json={
            "release_candidate_id": candidate_id,
            "verification_matrix_id": matrix_id,
            "owner_scope": ["workspace:main"],
            "run_service_checks": False,
            "check_results": [
                {
                    "verification_check_id": "check-api",
                    "check_key": "tests.brain",
                    "check_type": "unit_tests",
                    "status": "passed",
                    "severity": "low",
                    "required": True,
                    "passed": True,
                    "title": "Brain tests",
                    "summary": "passed",
                    "evidence": {"source": "test"},
                }
            ],
        },
    )
    run_id = run.json()["rc_run_id"]
    report_id = run.json()["result"]["rc_report_id"]
    pack_id = run.json()["evidence_pack_id"]

    responses = [
        candidate,
        client.get(f"/brain/rc/candidates/{candidate_id}", params={"scope": "workspace:main"}),
        client.get("/brain/rc/candidates", params={"scope": "workspace:main"}),
        matrix,
        client.get("/brain/rc/matrices", params={"scope": "workspace:main"}),
        client.post(
            "/brain/rc/matrices/seed-defaults",
            json={"scope": ["workspace:main"], "dry_run": True},
        ),
        run,
        client.get(f"/brain/rc/gate/runs/{run_id}", params={"scope": "workspace:main"}),
        client.get("/brain/rc/findings", params={"scope": "workspace:main"}),
        client.get("/brain/rc/evidence-packs", params={"scope": "workspace:main"}),
        client.get(f"/brain/rc/evidence-packs/{pack_id}", params={"scope": "workspace:main"}),
        client.get("/brain/rc/reports", params={"scope": "workspace:main"}),
        client.get(f"/brain/rc/reports/{report_id}", params={"scope": "workspace:main"}),
        client.post("/brain/rc/query", json={"scope": ["workspace:main"]}),
    ]

    assert [response.status_code for response in responses] == [200] * len(responses)
    assert run.json()["release_ready"] is True


def test_release_candidate_api_rejects_invalid_candidate_key() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/rc/candidates",
        json={
            "rc_key": "Bad Key",
            "version": "0.1.0",
            "owner_scope": ["workspace:main"],
        },
    )

    assert response.status_code == 422
