"""Model output governance API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.model_outputs import (
    ModelOutputCreateRequest,
    ModelOutputRecord,
    ModelOutputSegment,
    ResponseCandidate,
    StructuredOutputValidation,
    ToolIntentCandidate,
)
from aion_brain.contracts.output_governance import (
    ModelOutputQuery,
    ModelOutputQueryResult,
    OutputGovernanceRequest,
    OutputGovernanceRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/model-outputs", tags=["model-outputs"])


class DeleteOutputRequest(BaseModel):
    """Soft delete body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class StructuredValidationRequest(BaseModel):
    """Structured validation body."""

    model_config = ConfigDict(extra="forbid")

    schema_name: str | None = None


class CandidatePromotionRequest(BaseModel):
    """Response candidate promotion body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    approval_present: bool = False
    reason: str = Field(default="operator_requested", min_length=1)


class ToolIntentRejectRequest(BaseModel):
    """Tool intent rejection body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


@router.post("", response_model=ModelOutputRecord)
def create_model_output(
    body: ModelOutputCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelOutputRecord:
    """Receive a redacted model output record."""

    try:
        return container.output_governance_service.with_actor_context(actor_context).receive_output(
            _with_scope(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/query", response_model=ModelOutputQueryResult)
def query_model_outputs(
    body: ModelOutputQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelOutputQueryResult:
    """Query model output governance records."""

    try:
        return container.model_output_query_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/governance/{output_governance_id}", response_model=OutputGovernanceRun)
def get_governance_run(
    output_governance_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OutputGovernanceRun:
    """Return one output governance run."""

    run = container.output_governance_service.get_governance_run(output_governance_id)
    if run is None:
        raise HTTPException(status_code=404, detail="output_governance_not_found")
    try:
        authorize(
            container.policy_adapter,
            action_type="model_output.read",
            resource_type="output_governance",
            resource_id=output_governance_id,
            scope=run.owner_scope,
            trace_id=run.trace_id or actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            risk_level="low",
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    return run


@router.get("/response-candidates", response_model=list[ResponseCandidate])
def list_response_candidates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    trace_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ResponseCandidate]:
    """List response candidates."""

    try:
        return container.response_candidate_service.with_actor_context(
            actor_context
        ).list_candidates(
            _scope(scope, actor_context), status=status, trace_id=trace_id, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/response-candidates/{response_candidate_id}/promote",
    response_model=ResponseCandidate,
)
def promote_response_candidate(
    response_candidate_id: str,
    body: CandidatePromotionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResponseCandidate:
    """Promote a response candidate to a local ResponseDraft."""

    try:
        return container.response_candidate_service.with_actor_context(
            actor_context
        ).promote_to_response(
            response_candidate_id,
            actor_id=body.actor_id,
            approval_present=body.approval_present,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tool-intents", response_model=list[ToolIntentCandidate])
def list_tool_intents(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    trace_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ToolIntentCandidate]:
    """List captured tool intents."""

    try:
        return container.tool_intent_capture_service.with_actor_context(
            actor_context
        ).list_tool_intents(
            _scope(scope, actor_context), status=status, trace_id=trace_id, limit=limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/tool-intents/{tool_intent_id}/reject", response_model=ToolIntentCandidate)
def reject_tool_intent(
    tool_intent_id: str,
    body: ToolIntentRejectRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ToolIntentCandidate:
    """Reject a captured tool intent."""

    try:
        return container.tool_intent_capture_service.with_actor_context(
            actor_context
        ).reject_tool_intent(tool_intent_id, actor_id=body.actor_id, reason=body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{model_output_id}", response_model=ModelOutputRecord)
def get_model_output(
    model_output_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModelOutputRecord:
    """Return one redacted model output record."""

    try:
        output = container.output_governance_service.with_actor_context(actor_context).get_output(
            model_output_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if output is None:
        raise HTTPException(status_code=404, detail="model_output_not_found")
    return output


@router.delete("/{model_output_id}")
def delete_model_output(
    model_output_id: str,
    body: Annotated[DeleteOutputRequest, Body()],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft delete one model output."""

    try:
        deleted = container.output_governance_service.with_actor_context(
            actor_context
        ).soft_delete_output(model_output_id, actor_id=body.actor_id, reason=body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    return {"deleted": deleted, "model_output_id": model_output_id}


@router.post("/{model_output_id}/govern", response_model=OutputGovernanceRun)
def govern_model_output(
    model_output_id: str,
    body: OutputGovernanceRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OutputGovernanceRun:
    """Run model output governance."""

    request = body.model_copy(update={"model_output_id": model_output_id})
    try:
        return container.output_governance_service.with_actor_context(actor_context).govern(
            _governance_with_scope(request, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{model_output_id}/segments", response_model=list[ModelOutputSegment])
def list_segments(
    model_output_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ModelOutputSegment]:
    """Return parsed model output segments."""

    try:
        authorize(
            container.policy_adapter,
            action_type="model_output.parse",
            resource_type="model_output",
            resource_id=model_output_id,
            scope=_scope(scope, actor_context),
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            risk_level="low",
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    return container.model_output_repository.list_segments(model_output_id)


@router.post("/{model_output_id}/validate-structured", response_model=StructuredOutputValidation)
def validate_structured(
    model_output_id: str,
    body: StructuredValidationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> StructuredOutputValidation:
    """Validate structured JSON content from one model output."""

    try:
        authorize(
            container.policy_adapter,
            action_type="model_output.structured_validate",
            resource_type="model_output",
            resource_id=model_output_id,
            scope=_scope(scope, actor_context),
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            risk_level="low",
        )
        return container.structured_output_validator.validate(model_output_id, body.schema_name)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    if scope:
        return scope
    if actor_context.security_scope:
        return actor_context.security_scope
    if actor_context.workspace_id:
        return [f"workspace:{actor_context.workspace_id}"]
    return ["workspace:main"]


def _with_scope(
    body: ModelOutputCreateRequest, actor_context: ActorContext
) -> ModelOutputCreateRequest:
    updates: dict[str, object] = {}
    if not body.owner_scope:
        updates["owner_scope"] = _scope(None, actor_context)
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    return body.model_copy(update=updates) if updates else body


def _governance_with_scope(
    body: OutputGovernanceRequest,
    actor_context: ActorContext,
) -> OutputGovernanceRequest:
    if body.owner_scope:
        return body
    return body.model_copy(update={"owner_scope": _scope(None, actor_context)})


__all__ = ["router"]
