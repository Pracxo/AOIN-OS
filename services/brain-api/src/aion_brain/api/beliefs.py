"""Belief State Manager API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.beliefs import (
    BeliefClaim,
    BeliefClaimCreateRequest,
    BeliefContradiction,
    BeliefDeleteRequest,
    BeliefQuery,
    BeliefQueryResult,
    BeliefResolveRequest,
    BeliefReviseRequest,
    BeliefRevision,
    BeliefSupport,
    BeliefSupportCreateRequest,
    ClaimExtractionRequest,
    ClaimExtractionResult,
    TruthMaintenanceRequest,
    TruthMaintenanceRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/beliefs", tags=["beliefs"])


@router.post("/claims", response_model=BeliefClaim)
def create_claim(
    body: BeliefClaimCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BeliefClaim:
    """Create one explicit belief claim."""
    try:
        return container.belief_service.create_claim(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/claims/{claim_id}", response_model=BeliefClaim)
def get_claim(
    claim_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BeliefClaim:
    """Return one belief claim."""
    try:
        claim = container.belief_service.get_claim(claim_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if claim is None:
        raise HTTPException(status_code=404, detail="belief_claim_not_found")
    return claim


@router.post("/query", response_model=BeliefQueryResult)
def query_beliefs(
    body: BeliefQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BeliefQueryResult:
    """Query belief claims."""
    try:
        return container.belief_query_service.query(
            body.model_copy(update={"scope": body.scope or actor_context.security_scope})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/claims/{claim_id}/revise", response_model=BeliefRevision)
def revise_claim(
    claim_id: str,
    body: BeliefReviseRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BeliefRevision:
    """Revise one claim."""
    try:
        return container.belief_service.revise_claim(
            claim_id,
            body.to_status,
            body.new_confidence,
            body.reason,
            body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/claims/{claim_id}")
def delete_claim(
    claim_id: str,
    body: BeliefDeleteRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft-delete one claim."""
    try:
        deleted = container.belief_service.soft_delete_claim(
            claim_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": deleted, "claim_id": claim_id}


@router.post("/supports", response_model=BeliefSupport)
def create_support(
    body: BeliefSupportCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> BeliefSupport:
    """Create a support relation."""
    try:
        return container.belief_support_service.create_support(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/claims/{claim_id}/supports", response_model=list[BeliefSupport])
def list_supports(
    claim_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> list[BeliefSupport]:
    """List supports for one claim."""
    try:
        return container.belief_support_service.list_supports(claim_id)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/contradictions", response_model=list[BeliefContradiction])
def list_contradictions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[BeliefContradiction]:
    """List open or resolved contradictions."""
    try:
        return container.belief_contradiction_service.list_contradictions(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/contradictions/{contradiction_id}/resolve",
    response_model=BeliefContradiction,
)
def resolve_contradiction(
    contradiction_id: str,
    body: BeliefResolveRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BeliefContradiction:
    """Resolve one contradiction."""
    try:
        return container.belief_contradiction_service.resolve(
            contradiction_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/extract", response_model=ClaimExtractionResult)
def extract_claims(
    body: ClaimExtractionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ClaimExtractionResult:
    """Extract claims deterministically without LLM calls."""
    try:
        _authorize_extract(container, body, actor_context)
        return container.claim_extractor.extract(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/truth-maintenance/run", response_model=TruthMaintenanceRun)
def run_truth_maintenance(
    body: TruthMaintenanceRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> TruthMaintenanceRun:
    """Run deterministic truth maintenance."""
    try:
        return container.truth_maintenance_service.run(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/truth-maintenance/{truth_run_id}", response_model=TruthMaintenanceRun)
def get_truth_maintenance(
    truth_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> TruthMaintenanceRun:
    """Return one truth maintenance run."""
    run = container.truth_maintenance_service.get(truth_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="truth_maintenance_run_not_found")
    return run


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value


def _authorize_extract(
    container: KernelContainer,
    body: ClaimExtractionRequest,
    actor_context: ActorContext,
) -> None:
    from aion_brain.dialogue._shared import authorize

    authorize(
        container.policy_adapter,
        action_type="belief.claim.extract",
        resource_type="claim_extraction",
        resource_id=body.source_id,
        scope=body.owner_scope or actor_context.security_scope,
        trace_id=body.trace_id or actor_context.trace_id,
        actor_id=actor_context.actor_id,
        workspace_id=actor_context.workspace_id,
        risk_level="low",
        context={"source_type": body.source_type, "explicit_request": True},
    )
