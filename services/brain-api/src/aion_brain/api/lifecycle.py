"""Data Lifecycle Manager API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.lifecycle import (
    ArchiveCandidate,
    LifecycleEvaluationRequest,
    LifecycleEvaluationRun,
    LifecycleReport,
    LifecycleReviewRecord,
    PurgePreview,
    RedactionCandidate,
)
from aion_brain.contracts.retention import (
    LifecyclePolicy,
    LifecyclePolicyCreateRequest,
    RetentionClassification,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/lifecycle", tags=["lifecycle"])


class SeedPoliciesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    dry_run: bool = True


class CandidateMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    approval_present: bool = False
    reason: str = Field(min_length=1)


class PurgePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_uris: list[str] = Field(default_factory=list)
    scope: list[str] | None = None
    trace_id: str | None = None
    created_by: str | None = None


class LifecycleReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_type: str
    candidate_id: str
    decision: str = "manual_review"
    actor_id: str | None = None
    reason: str = Field(min_length=1)
    approval_present: bool = False


class LifecycleReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    trace_id: str | None = None
    created_by: str | None = None


@router.post("/policies", response_model=LifecyclePolicy)
def create_policy(
    body: LifecyclePolicyCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LifecyclePolicy:
    try:
        return container.lifecycle_policy_service.with_actor_context(actor_context).create_policy(
            body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/policies/seed-defaults")
def seed_policies(
    body: SeedPoliciesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    try:
        return container.lifecycle_policy_service.with_actor_context(
            actor_context
        ).seed_default_policies(_scope(body.scope, actor_context), dry_run=body.dry_run)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/policies", response_model=list[LifecyclePolicy])
def list_policies(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    policy_type: str | None = None,
    retention_class: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[LifecyclePolicy]:
    try:
        return container.lifecycle_policy_service.with_actor_context(actor_context).list_policies(
            _scope(scope, actor_context),
            status=status,
            policy_type=policy_type,
            retention_class=retention_class,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/policies/{lifecycle_policy_id}", response_model=LifecyclePolicy)
def get_policy(
    lifecycle_policy_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> LifecyclePolicy:
    try:
        policy = container.lifecycle_policy_service.with_actor_context(actor_context).get_policy(
            lifecycle_policy_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if policy is None:
        raise HTTPException(status_code=404, detail="lifecycle_policy_not_found")
    return policy


@router.post("/evaluate", response_model=LifecycleEvaluationRun)
def evaluate(
    body: LifecycleEvaluationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LifecycleEvaluationRun:
    try:
        return container.lifecycle_evaluator.with_actor_context(actor_context).evaluate(
            body.model_copy(
                update={
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/evaluations/{lifecycle_evaluation_id}", response_model=LifecycleEvaluationRun)
def get_evaluation(
    lifecycle_evaluation_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> LifecycleEvaluationRun:
    try:
        run = container.lifecycle_evaluator.with_actor_context(actor_context).get_evaluation(
            lifecycle_evaluation_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=404, detail="lifecycle_evaluation_not_found")
    return run


@router.get("/classifications", response_model=list[RetentionClassification])
def list_classifications(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    retention_class: str | None = None,
    lifecycle_state: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RetentionClassification]:
    try:
        return container.retention_classifier.with_actor_context(
            actor_context
        ).list_classifications(
            _scope(scope, actor_context),
            retention_class=retention_class,
            lifecycle_state=lifecycle_state,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/archive-candidates", response_model=list[ArchiveCandidate])
def list_archive_candidates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ArchiveCandidate]:
    try:
        return container.archive_planner.with_actor_context(actor_context).list_candidates(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/archive-candidates/{archive_candidate_id}/dismiss", response_model=ArchiveCandidate)
def dismiss_archive_candidate(
    archive_candidate_id: str,
    body: CandidateMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ArchiveCandidate:
    try:
        return container.archive_planner.with_actor_context(actor_context).dismiss_candidate(
            archive_candidate_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/archive-candidates/{archive_candidate_id}/convert-to-action-proposal",
    response_model=ArchiveCandidate,
)
def convert_archive_candidate(
    archive_candidate_id: str,
    body: CandidateMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ArchiveCandidate:
    try:
        return container.archive_planner.with_actor_context(
            actor_context
        ).convert_to_action_proposal(
            archive_candidate_id,
            body.actor_id or actor_context.actor_id,
            body.approval_present,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/redaction-candidates", response_model=list[RedactionCandidate])
def list_redaction_candidates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RedactionCandidate]:
    try:
        return container.redaction_planner.with_actor_context(actor_context).list_candidates(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/redaction-candidates/{redaction_candidate_id}/dismiss",
    response_model=RedactionCandidate,
)
def dismiss_redaction_candidate(
    redaction_candidate_id: str,
    body: CandidateMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RedactionCandidate:
    try:
        return container.redaction_planner.with_actor_context(actor_context).dismiss_candidate(
            redaction_candidate_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/redaction-candidates/{redaction_candidate_id}/convert-to-action-proposal",
    response_model=RedactionCandidate,
)
def convert_redaction_candidate(
    redaction_candidate_id: str,
    body: CandidateMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RedactionCandidate:
    try:
        return container.redaction_planner.with_actor_context(
            actor_context
        ).convert_to_action_proposal(
            redaction_candidate_id,
            body.actor_id or actor_context.actor_id,
            body.approval_present,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/purge-preview", response_model=PurgePreview)
def create_purge_preview(
    body: PurgePreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PurgePreview:
    try:
        return container.purge_preview_service.with_actor_context(actor_context).create_preview(
            body.resource_uris,
            _scope(body.scope, actor_context),
            trace_id=body.trace_id or actor_context.trace_id,
            created_by=body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/purge-previews", response_model=list[PurgePreview])
def list_purge_previews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PurgePreview]:
    try:
        return container.purge_preview_service.with_actor_context(actor_context).list_previews(
            _scope(scope, actor_context),
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/reviews", response_model=LifecycleReviewRecord)
def review_candidate(
    body: LifecycleReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LifecycleReviewRecord:
    try:
        return container.lifecycle_review_service.with_actor_context(
            actor_context
        ).review_candidate(
            body.candidate_type,
            body.candidate_id,
            body.decision,
            body.actor_id or actor_context.actor_id,
            body.reason,
            approval_present=body.approval_present,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews", response_model=list[LifecycleReviewRecord])
def list_reviews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    candidate_type: str | None = None,
    decision: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[LifecycleReviewRecord]:
    try:
        return container.lifecycle_review_service.with_actor_context(actor_context).list_reviews(
            _scope(scope, actor_context),
            candidate_type=candidate_type,
            decision=decision,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/report", response_model=LifecycleReport)
def generate_report(
    body: LifecycleReportRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LifecycleReport:
    try:
        return container.lifecycle_report_service.with_actor_context(actor_context).generate(
            _scope(body.scope, actor_context),
            trace_id=body.trace_id or actor_context.trace_id,
            created_by=body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
