"""Scenario harness and demo fixture APIs."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.scenarios import (
    DemoFixture,
    DemoFixtureLoadRequest,
    DemoFixtureLoadResult,
    ScenarioCreateRequest,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.scenarios.comparator import ScenarioComparator
from aion_brain.scenarios.fixtures import DemoFixtureService
from aion_brain.scenarios.repository import ScenarioRepository
from aion_brain.scenarios.runner import ScenarioRunner, require_scenarios_enabled

router = APIRouter(tags=["scenarios"])


def get_scenario_repository() -> ScenarioRepository:
    """Return the configured scenario repository."""
    return get_cached_scenario_repository(get_settings().database_url)


@lru_cache
def get_cached_scenario_repository(database_url: str) -> ScenarioRepository:
    """Return a cached scenario repository."""
    return ScenarioRepository(database_url)


def get_scenario_runner() -> ScenarioRunner:
    """Return the configured scenario runner."""
    settings = get_settings()
    return ScenarioRunner(
        get_cached_scenario_repository(settings.database_url),
        ScenarioComparator(),
        OPAAdapter(settings.opa_url),
        settings=settings,
    )


def get_demo_fixture_service() -> DemoFixtureService:
    """Return the configured demo fixture service."""
    settings = get_settings()
    return DemoFixtureService(
        get_cached_scenario_repository(settings.database_url),
        OPAAdapter(settings.opa_url),
    )


@router.post("/brain/scenarios", response_model=ScenarioDefinition)
def create_scenario(
    request: ScenarioCreateRequest,
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ScenarioDefinition:
    """Create a scenario definition."""
    require_scenarios_enabled(settings)
    request = request.model_copy(
        update={
            "created_by": request.created_by or actor_context.actor_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    return runner.create_scenario(request)


@router.get("/brain/scenarios", response_model=list[ScenarioDefinition])
def list_scenarios(
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    settings: Annotated[Settings, Depends(get_settings)],
    status: str | None = None,
    scenario_type: str | None = None,
    tags: Annotated[list[str] | None, Query()] = None,
) -> list[ScenarioDefinition]:
    """List active and persisted scenario definitions."""
    require_scenarios_enabled(settings)
    return runner.list_scenarios(status=status, scenario_type=scenario_type, tags=tags or [])


@router.post("/brain/scenarios/run", response_model=ScenarioRun)
def run_scenario(
    request: ScenarioRunRequest,
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ScenarioRun:
    """Run a scenario in dry-run mode by default."""
    require_scenarios_enabled(settings)
    request = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "created_by": request.created_by or actor_context.actor_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    return runner.run(request)


@router.get("/brain/scenarios/runs/{scenario_run_id}", response_model=ScenarioRun)
def get_scenario_run(
    scenario_run_id: str,
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ScenarioRun:
    """Return a scenario run."""
    require_scenarios_enabled(settings)
    run = runner.get_run(scenario_run_id, _scope(scope, actor_context))
    if run is None:
        raise HTTPException(status_code=404, detail="scenario_run_not_found")
    return run


@router.get("/brain/scenarios/runs", response_model=list[ScenarioRun])
def list_scenario_runs(
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    scenario_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[ScenarioRun]:
    """List recent scenario runs."""
    require_scenarios_enabled(settings)
    return runner.list_runs(
        _scope(scope, actor_context),
        status=status,
        scenario_type=scenario_type,
        limit=limit,
    )


@router.post("/brain/scenarios/seed-defaults", response_model=dict)
def seed_default_scenarios(
    request: dict[str, object],
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    """Seed built-in scenario definitions."""
    require_scenarios_enabled(settings)
    scope = _scope(_list_or_none(request.get("scope")), actor_context)
    dry_run = bool(request.get("dry_run", True))
    return runner.seed_default_scenarios(scope, dry_run=dry_run)


@router.get("/brain/scenarios/{scenario_id}", response_model=ScenarioDefinition)
def get_scenario(
    scenario_id: str,
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ScenarioDefinition:
    """Return one scenario definition."""
    require_scenarios_enabled(settings)
    scenario = runner.get_scenario(scenario_id, _scope(scope, actor_context))
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario_not_found")
    return scenario


@router.post("/brain/scenarios/{scenario_id}/disable", response_model=ScenarioDefinition)
def disable_scenario(
    scenario_id: str,
    request: dict[str, str],
    runner: Annotated[ScenarioRunner, Depends(get_scenario_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ScenarioDefinition:
    """Disable a scenario definition."""
    require_scenarios_enabled(settings)
    return runner.disable_scenario(
        scenario_id,
        request.get("actor_id") or actor_context.actor_id,
        request.get("reason") or "disabled_by_request",
    )


@router.get("/brain/demo-fixtures", response_model=list[DemoFixture])
def list_demo_fixtures(
    service: Annotated[DemoFixtureService, Depends(get_demo_fixture_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    fixture_type: str | None = None,
) -> list[DemoFixture]:
    """List default and loaded demo fixtures."""
    request_scope = _scope(scope, actor_context)
    defaults = service.list_default_fixtures(request_scope)
    loaded = service.list_loaded(request_scope, fixture_type=fixture_type)
    fixtures = [*loaded, *defaults]
    if fixture_type:
        fixtures = [fixture for fixture in fixtures if fixture.fixture_type == fixture_type]
    return fixtures


@router.post("/brain/demo-fixtures/load", response_model=DemoFixtureLoadResult)
def load_demo_fixture(
    request: DemoFixtureLoadRequest,
    service: Annotated[DemoFixtureService, Depends(get_demo_fixture_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DemoFixtureLoadResult:
    """Load one generic demo fixture."""
    if not request.owner_scope:
        request = request.model_copy(update={"owner_scope": actor_context.security_scope})
    return service.load(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value


def _list_or_none(value: object) -> list[str] | None:
    if isinstance(value, list):
        return [str(item) for item in value]
    return None
