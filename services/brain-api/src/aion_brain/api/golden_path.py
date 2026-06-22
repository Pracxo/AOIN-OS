"""Golden Path Scenario Harness API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.golden_path import (
    GoldenPathFixturePack,
    GoldenPathQuery,
    GoldenPathReport,
    GoldenPathRun,
    GoldenPathRunRequest,
    GoldenPathScenario,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/golden-path", tags=["golden-path"])


@router.post("/scenarios/seed-defaults")
def seed_default_scenarios(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Seed default golden path scenarios."""

    return container.golden_path_scenario_catalog.seed_default_scenarios(
        _scope(scope, actor_context),
        dry_run=dry_run,
        created_by=actor_context.actor_id,
    )


@router.post("/scenarios", response_model=GoldenPathScenario)
def create_scenario(
    body: GoldenPathScenario,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GoldenPathScenario:
    """Create or replace a golden path scenario."""

    return container.golden_path_scenario_catalog.create_scenario(
        body.model_copy(
            update={
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
    )


@router.get("/scenarios/{scenario_key}", response_model=GoldenPathScenario)
def get_scenario(
    scenario_key: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> GoldenPathScenario:
    """Return one golden path scenario."""

    scenario = container.golden_path_scenario_catalog.get_scenario(
        scenario_key,
        _scope(scope, actor_context),
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="golden_path_scenario_not_found")
    return scenario


@router.get("/scenarios", response_model=list[GoldenPathScenario])
def list_scenarios(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    scenario_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[GoldenPathScenario]:
    """List golden path scenarios."""

    return container.golden_path_scenario_catalog.list_scenarios(
        _scope(scope, actor_context),
        status=status,
        scenario_type=scenario_type,
        limit=limit,
    )


@router.post("/fixtures/seed-defaults")
def seed_default_fixtures(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Seed default synthetic fixture packs."""

    return container.golden_path_fixture_service.seed_default_fixture_packs(
        _scope(scope, actor_context),
        dry_run=dry_run,
        created_by=actor_context.actor_id,
    )


@router.get("/fixtures", response_model=list[GoldenPathFixturePack])
def list_fixtures(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[GoldenPathFixturePack]:
    """List golden path fixture packs."""

    return container.golden_path_fixture_service.list_fixture_packs(
        _scope(scope, actor_context),
        status=status,
        limit=limit,
    )


@router.post("/run", response_model=GoldenPathRun)
def run_golden_path(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    body: Annotated[dict[str, Any] | None, Body()] = None,
) -> GoldenPathRun:
    """Run deterministic golden path scenarios."""

    payload = dict(body or {})
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("actor_id", actor_context.actor_id)
    payload.setdefault("workspace_id", actor_context.workspace_id)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    payload.setdefault(
        "create_notifications",
        container.settings.golden_path_create_notifications_default,
    )
    payload.setdefault(
        "create_operator_items",
        container.settings.golden_path_create_operator_items_default,
    )
    return container.golden_path_runner.run(GoldenPathRunRequest.model_validate(payload))


@router.get("/runs/{golden_path_run_id}", response_model=GoldenPathRun)
def get_run(
    golden_path_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> GoldenPathRun:
    """Return one golden path run."""

    run = container.golden_path_runner.get_run(
        golden_path_run_id,
        _scope(scope, actor_context),
    )
    if run is None:
        raise HTTPException(status_code=404, detail="golden_path_run_not_found")
    return run


@router.get("/runs", response_model=list[GoldenPathRun])
def list_runs(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    trace_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[GoldenPathRun]:
    """List golden path runs."""

    return container.golden_path_runner.list_runs(
        _scope(scope, actor_context),
        status=status,
        trace_id=trace_id,
        limit=limit,
    )


@router.post("/release-smoke")
def release_smoke(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Run local release smoke matrix."""

    return container.golden_path_release_smoke.run(
        _scope(scope, actor_context),
        created_by=actor_context.actor_id,
    )


@router.get("/reports/{golden_path_report_id}", response_model=GoldenPathReport)
def get_report(
    golden_path_report_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> GoldenPathReport:
    """Return one golden path report."""

    report = container.golden_path_report_service.get_report(
        golden_path_report_id,
        _scope(scope, actor_context),
    )
    if report is None:
        raise HTTPException(status_code=404, detail="golden_path_report_not_found")
    return report


@router.get("/reports", response_model=list[GoldenPathReport])
def list_reports(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[GoldenPathReport]:
    """List golden path reports."""

    return container.golden_path_report_service.list_reports(
        _scope(scope, actor_context),
        status=status,
        limit=limit,
    )


@router.post("/query")
def query_golden_path(
    body: GoldenPathQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Query golden path records."""

    return container.golden_path_query_service.query(
        body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
