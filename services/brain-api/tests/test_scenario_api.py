"""Scenario API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.scenarios import get_demo_fixture_service, get_scenario_runner
from aion_brain.contracts.scenarios import (
    DemoFixture,
    DemoFixtureLoadResult,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioStep,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeRunner:
    def create_scenario(self, request):
        return scenario(request.scenario_id or "scenario-1")

    def list_scenarios(self, status=None, scenario_type=None, tags=None):
        return [scenario("golden_path_brain")]

    def get_scenario(self, scenario_id: str, scope: list[str]):
        return scenario(scenario_id)

    def disable_scenario(self, scenario_id: str, actor_id: str | None, reason: str):
        return scenario(scenario_id).model_copy(update={"status": "disabled"})

    def run(self, request):
        return scenario_run(request.scenario_id or "inline")

    def get_run(self, scenario_run_id: str, scope: list[str]):
        return scenario_run("golden_path_brain", scenario_run_id=scenario_run_id)

    def list_runs(self, scope, status=None, scenario_type=None, limit=50):
        return [scenario_run("golden_path_brain")]

    def seed_default_scenarios(self, scope: list[str], dry_run: bool = True):
        return {"dry_run": dry_run, "scenario_ids": ["golden_path_brain"], "seeded": 0}


class FakeFixtureService:
    def list_default_fixtures(self, scope: list[str]):
        return [fixture("generic_event")]

    def list_loaded(self, scope: list[str], fixture_type: str | None = None):
        return []

    def load(self, request):
        return DemoFixtureLoadResult(
            fixture_id=request.fixture_id or "generic_event",
            loaded=False,
            dry_run=True,
            result={"planned_records": ["aion_event"]},
            reason="dry_run",
            created_at=datetime.now(UTC),
        )


def test_scenario_api_routes_work() -> None:
    app.dependency_overrides[get_scenario_runner] = lambda: FakeRunner()
    app.dependency_overrides[get_demo_fixture_service] = lambda: FakeFixtureService()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        payload = {
            "name": "Scenario",
            "description": "Generic scenario.",
            "scenario_type": "smoke",
            "owner_scope": ["workspace:main"],
            "steps": [step().model_dump(mode="json")],
        }
        create = client.post("/brain/scenarios", json=payload)
        list_response = client.get("/brain/scenarios")
        get_response = client.get(
            "/brain/scenarios/golden_path_brain",
            params={"scope": "workspace:main"},
        )
        disable = client.post(
            "/brain/scenarios/golden_path_brain/disable",
            json={"actor_id": "actor-1", "reason": "test"},
        )
        run = client.post(
            "/brain/scenarios/run",
            json={"scenario_id": "golden_path_brain", "owner_scope": ["workspace:main"]},
        )
        get_run = client.get(
            "/brain/scenarios/runs/run-1",
            params={"scope": "workspace:main"},
        )
        runs = client.get("/brain/scenarios/runs", params={"scope": "workspace:main"})
        seed = client.post(
            "/brain/scenarios/seed-defaults",
            json={"scope": ["workspace:main"], "dry_run": True},
        )
        fixtures = client.get("/brain/demo-fixtures", params={"scope": "workspace:main"})
        load = client.post(
            "/brain/demo-fixtures/load",
            json={"fixture_id": "generic_event", "owner_scope": ["workspace:main"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert create.status_code == 200
    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert disable.status_code == 200
    assert run.status_code == 200
    assert get_run.status_code == 200
    assert runs.status_code == 200
    assert seed.status_code == 200
    assert fixtures.status_code == 200
    assert load.status_code == 200


def scenario(scenario_id: str) -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=scenario_id,
        name="Scenario",
        description="Generic scenario.",
        status="active",
        scenario_type="smoke",
        owner_scope=["workspace:main"],
        steps=[step()],
        expected={},
        tags=[],
        metadata={},
    )


def scenario_run(scenario_id: str, scenario_run_id: str = "run-1") -> ScenarioRun:
    now = datetime.now(UTC)
    return ScenarioRun(
        scenario_run_id=scenario_run_id,
        scenario_id=scenario_id,
        status="passed",
        mode="dry_run",
        owner_scope=["workspace:main"],
        step_count=1,
        passed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        steps=[],
        result={"status": "passed"},
        comparison={"passed": True},
        created_at=now,
        completed_at=now,
    )


def fixture(fixture_id: str) -> DemoFixture:
    return DemoFixture(
        fixture_id=fixture_id,
        name="Generic Event",
        description="Generic fixture.",
        status="active",
        fixture_type="event",
        owner_scope=["workspace:main"],
        content={},
        loaded=False,
        result={},
    )


def step() -> ScenarioStep:
    return ScenarioStep(
        step_id="step-1",
        step_type="noop",
        description="Noop.",
        request={},
        expected={"required_keys": ["status"]},
    )


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["scenario.read", "scenario.run"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
