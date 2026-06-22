"""Golden Path API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_golden_path_api_sequence() -> None:
    client = TestClient(create_app(kernel_container()))

    scenario_seed = client.post("/brain/golden-path/scenarios/seed-defaults")
    assert scenario_seed.status_code == 200
    assert scenario_seed.json()["dry_run"] is True
    assert len(scenario_seed.json()["scenarios"]) == 20

    fixture_seed = client.post("/brain/golden-path/fixtures/seed-defaults")
    assert fixture_seed.status_code == 200
    assert fixture_seed.json()["dry_run"] is True

    scenarios = client.get("/brain/golden-path/scenarios")
    assert scenarios.status_code == 200
    assert len(scenarios.json()) >= 20

    run_response = client.post(
        "/brain/golden-path/run",
        json={
            "scenario_keys": ["golden.boot.readiness"],
            "run_all_defaults": False,
            "mode": "dry_run",
        },
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["result"]["external_calls"] is False
    assert run["result"]["tool_execution"] is False
    assert run["report_id"]

    run_id = run["golden_path_run_id"]
    report_id = run["report_id"]
    assert client.get(f"/brain/golden-path/runs/{run_id}").status_code == 200
    assert client.get(f"/brain/golden-path/reports/{report_id}").status_code == 200
    assert client.get("/brain/golden-path/runs").status_code == 200
    assert client.get("/brain/golden-path/reports").status_code == 200

    query = client.post("/brain/golden-path/query", json={"scope": ["workspace:main"]})
    assert query.status_code == 200
    assert query.json()["total_count"] >= 1

    smoke = client.post("/brain/golden-path/release-smoke")
    assert smoke.status_code == 200
    assert smoke.json()["external_calls"] is False


def test_golden_path_api_rejects_domain_scenario() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/golden-path/scenarios",
        json={
            "golden_path_scenario_id": "scenario-1",
            "scenario_key": "golden.test",
            "name": "Finance Scenario",
            "description": "Generic dry-run verification.",
            "status": "active",
            "scenario_type": "generic",
            "owner_scope": ["workspace:main"],
        },
    )

    assert response.status_code == 422
