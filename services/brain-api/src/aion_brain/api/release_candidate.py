"""Release candidate gate API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.release_candidate import (
    RCEvidencePack,
    RCFinding,
    RCGateRun,
    RCGateRunRequest,
    RCQuery,
    RCReport,
    ReleaseCandidate,
    ReleaseCandidateCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.verification_matrix import (
    VerificationMatrix,
    VerificationMatrixCreateRequest,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/rc", tags=["release-candidate"])


class SeedMatricesRequest(BaseModel):
    """Seed default RC matrices."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True
    created_by: str | None = None


class DismissRCFindingRequest(BaseModel):
    """Dismiss an RC finding."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = "dismissed"


@router.post("/candidates", response_model=ReleaseCandidate)
def create_candidate(
    body: Annotated[dict[str, Any], Body()],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReleaseCandidate:
    """Create a local release candidate record."""

    payload = dict(body)
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("actor_id", actor_context.actor_id)
    payload.setdefault("workspace_id", actor_context.workspace_id)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    return container.release_candidate_service.create_candidate(
        _validate_contract(ReleaseCandidateCreateRequest, payload)
    )


@router.get("/candidates", response_model=list[ReleaseCandidate])
def list_candidates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    version: str | None = None,
    release_ready: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ReleaseCandidate]:
    """List release candidates."""

    return container.release_candidate_service.list_candidates(
        _scope(scope, actor_context),
        status=status,
        version=version,
        release_ready=release_ready,
        limit=limit,
    )


@router.get("/candidates/{release_candidate_id}", response_model=ReleaseCandidate)
def get_candidate(
    release_candidate_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReleaseCandidate:
    """Return one release candidate."""

    candidate = container.release_candidate_service.get_candidate(
        release_candidate_id,
        _scope(scope, actor_context),
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="release_candidate_not_found")
    return candidate


@router.post("/matrices", response_model=VerificationMatrix)
def create_matrix(
    body: Annotated[dict[str, Any], Body()],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> VerificationMatrix:
    """Create an RC verification matrix."""

    payload = dict(body)
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    return container.verification_matrix_service.create_matrix(
        _validate_contract(VerificationMatrixCreateRequest, payload)
    )


@router.get("/matrices", response_model=list[VerificationMatrix])
def list_matrices(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[VerificationMatrix]:
    """List RC verification matrices."""

    return container.verification_matrix_service.list_matrices(
        _scope(scope, actor_context),
        status=status,
        limit=limit,
    )


@router.post("/matrices/seed-defaults")
def seed_matrices(
    body: SeedMatricesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed the default RC matrix."""

    return container.verification_matrix_service.seed_default_matrices(
        _scope(body.scope, actor_context),
        dry_run=body.dry_run,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.post("/gate/run", response_model=RCGateRun)
def run_gate(
    body: Annotated[dict[str, Any], Body()],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RCGateRun:
    """Run the deterministic local RC gate."""

    payload = dict(body)
    payload.setdefault("owner_scope", actor_context.security_scope)
    payload.setdefault("actor_id", actor_context.actor_id)
    payload.setdefault("workspace_id", actor_context.workspace_id)
    payload.setdefault("trace_id", actor_context.trace_id)
    payload.setdefault("created_by", actor_context.actor_id)
    payload.setdefault("create_notifications", container.settings.rc_create_notifications_default)
    payload.setdefault("create_operator_items", container.settings.rc_create_operator_items_default)
    return container.rc_gate_service.run(_validate_contract(RCGateRunRequest, payload))


@router.get("/gate/runs/{rc_run_id}", response_model=RCGateRun)
def get_run(
    rc_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RCGateRun:
    """Return one RC gate run."""

    run = container.rc_gate_service.get_run(rc_run_id, _scope(scope, actor_context))
    if run is None:
        raise HTTPException(status_code=404, detail="rc_run_not_found")
    return run


@router.get("/findings", response_model=list[RCFinding])
def findings(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    blocking: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RCFinding]:
    """List RC findings."""

    return container.rc_finding_service.list_findings(
        _scope(scope, actor_context),
        status=status,
        severity=severity,
        blocking=blocking,
        limit=limit,
    )


@router.post("/findings/{rc_finding_id}/dismiss", response_model=RCFinding)
def dismiss_finding(
    rc_finding_id: str,
    body: DismissRCFindingRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RCFinding:
    """Dismiss an RC finding."""

    finding = container.rc_finding_service.dismiss_finding(
        rc_finding_id,
        _scope(scope, actor_context),
        actor_id=body.actor_id or actor_context.actor_id,
        reason=body.reason,
    )
    if finding is None:
        raise HTTPException(status_code=404, detail="rc_finding_not_found")
    return finding


@router.get("/evidence-packs", response_model=list[RCEvidencePack])
def list_evidence_packs(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[RCEvidencePack]:
    """List RC evidence packs."""

    return container.rc_evidence_pack_service.list_packs(
        _scope(scope, actor_context),
        status=status,
        limit=limit,
    )


@router.get("/evidence-packs/{evidence_pack_id}", response_model=RCEvidencePack)
def get_evidence_pack(
    evidence_pack_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RCEvidencePack:
    """Return one RC evidence pack."""

    pack = container.rc_evidence_pack_service.get_pack(
        evidence_pack_id,
        _scope(scope, actor_context),
    )
    if pack is None:
        raise HTTPException(status_code=404, detail="rc_evidence_pack_not_found")
    return pack


@router.get("/reports", response_model=list[RCReport])
def list_reports(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    version: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[RCReport]:
    """List RC reports."""

    return container.rc_report_service.list_reports(
        _scope(scope, actor_context),
        status=status,
        version=version,
        limit=limit,
    )


@router.get("/reports/{rc_report_id}", response_model=RCReport)
def get_report(
    rc_report_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RCReport:
    """Return one RC report."""

    report = container.rc_report_service.get_report(rc_report_id, _scope(scope, actor_context))
    if report is None:
        raise HTTPException(status_code=404, detail="rc_report_not_found")
    return report


@router.post("/query")
def query(
    body: Annotated[dict[str, Any], Body()],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Query RC-owned records."""

    payload = dict(body)
    payload.setdefault("scope", actor_context.security_scope)
    return container.rc_query_service.query(_validate_contract(RCQuery, payload))


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _validate_contract[T: BaseModel](model: type[T], payload: dict[str, Any]) -> T:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


__all__ = ["router"]
