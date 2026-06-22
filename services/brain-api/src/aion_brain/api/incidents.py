"""Incident correlation API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.incidents import (
    IncidentCorrelationRequest,
    IncidentCorrelationRule,
    IncidentCorrelationRun,
    IncidentCreateRequest,
    IncidentQuery,
    IncidentQueryResult,
    IncidentRecord,
    IncidentSignal,
    IncidentSignalCreateRequest,
)
from aion_brain.contracts.root_cause import (
    RecoveryReview,
    RecoveryReviewRequest,
    RootCauseCandidate,
    RootCauseCandidateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/incidents", tags=["incidents"])


class MutationReasonRequest(BaseModel):
    """Reason-bearing status mutation request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str


class SeedRulesRequest(BaseModel):
    """Default rule seeding request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    dry_run: bool = True


class GenerateRootCausesRequest(BaseModel):
    """Root cause generation request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    created_by: str | None = None


@router.post("/signals", response_model=IncidentSignal)
def create_signal(
    body: IncidentSignalCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentSignal:
    try:
        return container.incident_signal_service.with_actor_context(actor_context).create_signal(
            _signal_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/signals", response_model=list[IncidentSignal])
def list_signals(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    source_type: str | None = None,
    signal_type: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[IncidentSignal]:
    try:
        return container.incident_signal_service.with_actor_context(actor_context).list_signals(
            _scope(scope, actor_context),
            status=status,
            source_type=source_type,
            signal_type=signal_type,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/signals/{incident_signal_id}/dismiss", response_model=IncidentSignal)
def dismiss_signal(
    incident_signal_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentSignal:
    try:
        return container.incident_signal_service.with_actor_context(actor_context).dismiss_signal(
            incident_signal_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/query", response_model=IncidentQueryResult)
def query_incidents(
    body: IncidentQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> IncidentQueryResult:
    try:
        return container.incident_query_service.query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/rules", response_model=IncidentCorrelationRule)
def create_rule(
    body: IncidentCorrelationRule,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentCorrelationRule:
    try:
        return container.incident_rule_service.with_actor_context(actor_context).create_rule(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/rules", response_model=list[IncidentCorrelationRule])
def list_rules(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    rule_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[IncidentCorrelationRule]:
    try:
        return container.incident_rule_service.with_actor_context(actor_context).list_rules(
            _scope(scope, actor_context), status=status, rule_type=rule_type, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/rules/seed-defaults")
def seed_rules(
    body: SeedRulesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    try:
        return container.incident_rule_service.with_actor_context(actor_context).seed_default_rules(
            _scope(body.scope, actor_context), dry_run=body.dry_run
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/correlate", response_model=IncidentCorrelationRun)
def correlate(
    body: IncidentCorrelationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentCorrelationRun:
    try:
        return container.incident_correlation_engine.with_actor_context(actor_context).correlate(
            _correlation_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/correlation-runs/{correlation_run_id}", response_model=IncidentCorrelationRun)
def get_correlation_run(
    correlation_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> IncidentCorrelationRun:
    run = container.incident_correlation_engine.get_correlation_run(correlation_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="incident_correlation_run_not_found")
    return run


@router.post(
    "/{incident_id}/root-cause-candidates/generate",
    response_model=list[RootCauseCandidate],
)
def generate_root_causes(
    incident_id: str,
    body: GenerateRootCausesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[RootCauseCandidate]:
    try:
        return container.root_cause_candidate_service.with_actor_context(
            actor_context
        ).generate_for_incident(
            incident_id,
            _scope(body.scope, actor_context),
            created_by=body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/root-cause-candidates", response_model=RootCauseCandidate)
def create_root_cause(
    body: RootCauseCandidateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RootCauseCandidate:
    try:
        return container.root_cause_candidate_service.with_actor_context(
            actor_context
        ).create_candidate(_root_cause_with_context(body, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/root-cause-candidates", response_model=list[RootCauseCandidate])
def list_root_causes(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    incident_id: str | None = None,
    status: str | None = None,
    candidate_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RootCauseCandidate]:
    return container.root_cause_candidate_service.list_candidates(
        incident_id=incident_id, status=status, candidate_type=candidate_type, limit=limit
    )


@router.post(
    "/root-cause-candidates/{root_cause_candidate_id}/confirm",
    response_model=RootCauseCandidate,
)
def confirm_root_cause(
    root_cause_candidate_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RootCauseCandidate:
    try:
        return container.root_cause_candidate_service.with_actor_context(
            actor_context
        ).confirm_candidate(
            root_cause_candidate_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/root-cause-candidates/{root_cause_candidate_id}/dismiss",
    response_model=RootCauseCandidate,
)
def dismiss_root_cause(
    root_cause_candidate_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RootCauseCandidate:
    try:
        return container.root_cause_candidate_service.with_actor_context(
            actor_context
        ).dismiss_candidate(
            root_cause_candidate_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/recovery-reviews", response_model=RecoveryReview)
def create_recovery_review(
    body: RecoveryReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RecoveryReview:
    try:
        return container.recovery_review_service.with_actor_context(actor_context).create_review(
            _recovery_review_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/recovery-reviews", response_model=list[RecoveryReview])
def list_recovery_reviews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    incident_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RecoveryReview]:
    try:
        return container.recovery_review_service.with_actor_context(actor_context).list_reviews(
            _scope(scope, actor_context), incident_id=incident_id, status=status, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/recovery-reviews/{recovery_review_id}", response_model=RecoveryReview)
def get_recovery_review(
    recovery_review_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RecoveryReview:
    try:
        review = container.recovery_review_service.with_actor_context(actor_context).get_review(
            recovery_review_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if review is None:
        raise HTTPException(status_code=404, detail="recovery_review_not_found")
    return review


@router.post("", response_model=IncidentRecord)
def create_incident(
    body: IncidentCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentRecord:
    try:
        return container.incident_service.with_actor_context(actor_context).create_incident(
            _incident_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/{incident_id}", response_model=IncidentRecord)
def get_incident(
    incident_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> IncidentRecord:
    try:
        incident = container.incident_service.with_actor_context(actor_context).get_incident(
            incident_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if incident is None:
        raise HTTPException(status_code=404, detail="incident_not_found")
    return incident


@router.post("/{incident_id}/acknowledge", response_model=IncidentRecord)
def acknowledge_incident(
    incident_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentRecord:
    return _incident_update(container, actor_context, incident_id, body, "acknowledge")


@router.post("/{incident_id}/resolve", response_model=IncidentRecord)
def resolve_incident(
    incident_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentRecord:
    return _incident_update(container, actor_context, incident_id, body, "resolve")


@router.post("/{incident_id}/dismiss", response_model=IncidentRecord)
def dismiss_incident(
    incident_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentRecord:
    return _incident_update(container, actor_context, incident_id, body, "dismiss")


@router.post("/{incident_id}/archive", response_model=IncidentRecord)
def archive_incident(
    incident_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IncidentRecord:
    return _incident_update(container, actor_context, incident_id, body, "archive")


def _incident_update(
    container: KernelContainer,
    actor_context: ActorContext,
    incident_id: str,
    body: MutationReasonRequest,
    action: str,
) -> IncidentRecord:
    service = container.incident_service.with_actor_context(actor_context)
    try:
        actor_id = body.actor_id or actor_context.actor_id
        if action == "acknowledge":
            return service.acknowledge(incident_id, actor_id, body.reason)
        if action == "resolve":
            return service.resolve(incident_id, actor_id, body.reason)
        if action == "dismiss":
            return service.dismiss(incident_id, actor_id, body.reason)
        if action == "archive":
            return service.archive(incident_id, actor_id, body.reason)
        raise ValueError("unsupported_incident_action")
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _signal_with_context(
    body: IncidentSignalCreateRequest, actor_context: ActorContext
) -> IncidentSignalCreateRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "trace_id": body.trace_id or actor_context.trace_id,
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
        }
    )


def _incident_with_context(
    body: IncidentCreateRequest, actor_context: ActorContext
) -> IncidentCreateRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "trace_id": body.trace_id or actor_context.trace_id,
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
        }
    )


def _correlation_with_context(
    body: IncidentCorrelationRequest, actor_context: ActorContext
) -> IncidentCorrelationRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "trace_id": body.trace_id or actor_context.trace_id,
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
        }
    )


def _root_cause_with_context(
    body: RootCauseCandidateRequest, actor_context: ActorContext
) -> RootCauseCandidateRequest:
    return body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})


def _recovery_review_with_context(
    body: RecoveryReviewRequest, actor_context: ActorContext
) -> RecoveryReviewRequest:
    return body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
        }
    )


__all__ = ["router"]
