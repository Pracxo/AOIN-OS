"""First-run bootstrap and setup doctor API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.bootstrap import (
    BootstrapProfile,
    BootstrapRun,
    BootstrapRunRequest,
    SeedBundle,
    SeedExecutionRecord,
    SeedExecutionRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.setup_doctor import (
    SetupDoctorRequest,
    SetupDoctorResult,
    SetupFinding,
    SetupReport,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/bootstrap", tags=["bootstrap"])


class SeedDefaultsRequest(BaseModel):
    """Request to seed default bootstrap-owned metadata."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True
    created_by: str | None = None


class DismissFindingRequest(BaseModel):
    """Request to dismiss a setup finding."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = "dismissed"


@router.post("/profiles/seed-defaults")
def seed_default_profiles(
    body: SeedDefaultsRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Seed built-in bootstrap profiles."""

    return container.bootstrap_profile_service.seed_default_profiles(
        _scope(body.scope, actor_context),
        dry_run=body.dry_run,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.get("/profiles", response_model=list[BootstrapProfile])
def list_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    profile_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[BootstrapProfile]:
    """List bootstrap profiles."""

    return container.bootstrap_profile_service.list_profiles(
        _scope(scope, actor_context),
        status=status,
        profile_type=profile_type,
        limit=limit,
    )


@router.post("/seed-bundles/seed-defaults")
def seed_default_bundles(
    body: SeedDefaultsRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Seed built-in seed bundles."""

    return container.seed_bundle_service.seed_default_bundles(
        _scope(body.scope, actor_context),
        dry_run=body.dry_run,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.get("/seed-bundles", response_model=list[SeedBundle])
def list_seed_bundles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    bundle_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[SeedBundle]:
    """List seed bundles."""

    return container.seed_bundle_service.list_bundles(
        _scope(scope, actor_context),
        status=status,
        bundle_type=bundle_type,
        limit=limit,
    )


@router.post("/seed", response_model=SeedExecutionRecord)
def seed(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    body: Annotated[dict[str, Any], Body()],
) -> SeedExecutionRecord:
    """Execute one seed bundle."""

    payload = dict(body)
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("actor_id", actor_context.actor_id)
    payload.setdefault("workspace_id", actor_context.workspace_id)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    return container.seed_executor.execute(_validate_contract(SeedExecutionRequest, payload))


@router.post("/doctor", response_model=SetupDoctorResult)
def doctor(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    body: Annotated[dict[str, Any], Body()],
) -> SetupDoctorResult:
    """Run local setup doctor."""

    payload = dict(body)
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("actor_id", actor_context.actor_id)
    payload.setdefault("workspace_id", actor_context.workspace_id)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    return container.setup_doctor.run(_validate_contract(SetupDoctorRequest, payload))


@router.post("/run", response_model=BootstrapRun)
def run_bootstrap(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    body: Annotated[dict[str, Any], Body()],
) -> BootstrapRun:
    """Run first-run bootstrap."""

    payload = dict(body)
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("actor_id", actor_context.actor_id)
    payload.setdefault("workspace_id", actor_context.workspace_id)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    payload.setdefault(
        "create_notifications",
        container.settings.bootstrap_create_notifications_default,
    )
    payload.setdefault(
        "create_operator_items",
        container.settings.bootstrap_create_operator_items_default,
    )
    return container.bootstrap_runner.run(_validate_contract(BootstrapRunRequest, payload))


@router.get("/runs", response_model=list[BootstrapRun])
def list_runs(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    profile_key: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[BootstrapRun]:
    """List bootstrap runs."""

    return container.bootstrap_runner.list_runs(
        _scope(scope, actor_context),
        status=status,
        profile_key=profile_key,
        limit=limit,
    )


@router.get("/runs/{bootstrap_run_id}", response_model=BootstrapRun)
def get_run(
    bootstrap_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BootstrapRun:
    """Return one bootstrap run."""

    run = container.bootstrap_runner.get_run(bootstrap_run_id, _scope(scope, actor_context))
    if run is None:
        raise HTTPException(status_code=404, detail="bootstrap_run_not_found")
    return run


@router.get("/findings", response_model=list[SetupFinding])
def list_findings(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    category: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[SetupFinding]:
    """List setup findings."""

    return container.bootstrap_query_service.list_findings(
        _scope(scope, actor_context),
        status=status,
        severity=severity,
        category=category,
        limit=limit,
    )


@router.post("/findings/{setup_finding_id}/dismiss", response_model=SetupFinding)
def dismiss_finding(
    setup_finding_id: str,
    body: DismissFindingRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SetupFinding:
    """Dismiss one setup finding."""

    finding = container.bootstrap_query_service.dismiss_finding(
        setup_finding_id,
        _scope(scope, actor_context),
        actor_id=body.actor_id or actor_context.actor_id,
        reason=body.reason,
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="setup_finding_not_found")
    return finding


@router.get("/reports", response_model=list[SetupReport])
def list_reports(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[SetupReport]:
    """List setup reports."""

    return container.setup_report_service.list_reports(
        _scope(scope, actor_context),
        status=status,
        limit=limit,
    )


@router.get("/reports/{setup_report_id}", response_model=SetupReport)
def get_report(
    setup_report_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SetupReport:
    """Return one setup report."""

    report = container.setup_report_service.get_report(
        setup_report_id, _scope(scope, actor_context)
    )
    if report is None:
        raise HTTPException(status_code=404, detail="setup_report_not_found")
    return report


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _validate_contract(model: type[BaseModel], payload: dict[str, Any]) -> Any:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        detail = [
            {
                "loc": list(error.get("loc", ())),
                "msg": error.get("msg", "validation error"),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors(include_url=False, include_context=False)
        ]
        raise HTTPException(status_code=422, detail=detail) from exc


__all__ = ["router"]
