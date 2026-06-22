"""Instruction hierarchy and preference ledger API."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.instructions import (
    ConstraintRecord,
    InstructionConflict,
    InstructionCreateRequest,
    InstructionRecord,
    InstructionResolutionRequest,
    InstructionResolutionResult,
    StyleProfile,
    StyleProfileCreateRequest,
)
from aion_brain.contracts.preferences import (
    PreferenceCreateRequest,
    PreferenceLearningCandidate,
    PreferenceRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["instructions"])


class DisableRequest(BaseModel):
    """Disable request body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str | None = None


class ConflictResolutionRequest(BaseModel):
    """Conflict resolution request body."""

    model_config = ConfigDict(extra="forbid")

    resolution: str = Field(min_length=1)
    actor_id: str | None = None
    reason: str | None = None


@router.post("/brain/instructions/resolve", response_model=InstructionResolutionResult)
def resolve_instructions(
    body: InstructionResolutionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InstructionResolutionResult:
    """Resolve effective instructions for a scope."""

    try:
        return container.instruction_resolver.resolve(
            body.model_copy(update=_context_updates(body, actor_context))
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/instructions/conflicts", response_model=list[InstructionConflict])
def list_instruction_conflicts(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[InstructionConflict]:
    """List instruction conflicts."""

    try:
        return container.instruction_conflict_detector.list_conflicts(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/brain/instructions/conflicts/{conflict_id}/resolve",
    response_model=InstructionConflict,
)
def resolve_instruction_conflict(
    conflict_id: str,
    body: ConflictResolutionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InstructionConflict:
    """Resolve an instruction conflict."""

    try:
        return container.instruction_conflict_detector.resolve_conflict(
            conflict_id,
            resolution=body.resolution,
            actor_id=actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/instructions", response_model=InstructionRecord)
def create_instruction(
    body: InstructionCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InstructionRecord:
    """Create one instruction."""

    try:
        updated = body.model_copy(update=_context_updates(body, actor_context))
        normalized = _normalize_instruction_text(updated.instruction_text)
        return container.instruction_service.create_instruction(
            updated.to_record(
                updated.instruction_id or f"instruction-{uuid4().hex}",
                normalized,
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/instructions", response_model=list[InstructionRecord])
def list_instructions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    instruction_type: str | None = None,
    scope_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[InstructionRecord]:
    """List instructions."""

    try:
        return container.instruction_service.list_instructions(
            _scope(scope, actor_context),
            status=status,
            instruction_type=instruction_type,
            scope_type=scope_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/instructions/{instruction_id}", response_model=InstructionRecord)
def get_instruction(
    instruction_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> InstructionRecord:
    """Return one instruction."""

    try:
        instruction = container.instruction_service.get_instruction(
            instruction_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if instruction is None:
        raise HTTPException(status_code=404, detail="instruction_not_found")
    return instruction


@router.post("/brain/instructions/{instruction_id}/disable", response_model=InstructionRecord)
def disable_instruction(
    instruction_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InstructionRecord:
    """Disable one instruction."""

    try:
        return container.instruction_service.disable_instruction(
            instruction_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/preferences/candidates", response_model=PreferenceLearningCandidate)
def create_preference_candidate(
    body: PreferenceLearningCandidate,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceLearningCandidate:
    """Create one explicit preference learning candidate."""

    try:
        return container.preference_learning_service.propose_candidate(
            body.model_copy(update=_context_updates(body, actor_context))
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/preferences/candidates", response_model=list[PreferenceLearningCandidate])
def list_preference_candidates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    preference_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PreferenceLearningCandidate]:
    """List preference candidates."""

    try:
        return container.preference_learning_service.list_candidates(
            _scope(scope, actor_context),
            status=status,
            preference_type=preference_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/brain/preferences/candidates/{candidate_id}/confirm",
    response_model=PreferenceRecord,
)
def confirm_preference_candidate(
    candidate_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceRecord:
    """Confirm a preference candidate."""

    try:
        return container.preference_learning_service.confirm_candidate(
            candidate_id,
            actor_id=actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/brain/preferences/candidates/{candidate_id}/reject",
    response_model=PreferenceLearningCandidate,
)
def reject_preference_candidate(
    candidate_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceLearningCandidate:
    """Reject a preference candidate."""

    try:
        return container.preference_learning_service.reject_candidate(
            candidate_id,
            actor_id=actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/preferences", response_model=PreferenceRecord)
def create_preference(
    body: PreferenceCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceRecord:
    """Create one preference."""

    try:
        updated = body.model_copy(update=_context_updates(body, actor_context))
        return container.preference_service.create_preference(
            updated.to_record(updated.preference_id or f"preference-{uuid4().hex}")
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/preferences", response_model=list[PreferenceRecord])
def list_preferences(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    status: str | None = None,
    preference_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PreferenceRecord]:
    """List preferences."""

    try:
        return container.preference_service.list_preferences(
            _scope(scope, actor_context),
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
            preference_type=preference_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/preferences/{preference_id}/confirm", response_model=PreferenceRecord)
def confirm_preference(
    preference_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceRecord:
    """Confirm a preference."""

    try:
        return container.preference_service.confirm_preference(
            preference_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/preferences/{preference_id}/reject", response_model=PreferenceRecord)
def reject_preference(
    preference_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceRecord:
    """Reject a preference."""

    try:
        return container.preference_service.reject_preference(
            preference_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/preferences/{preference_id}/disable", response_model=PreferenceRecord)
def disable_preference(
    preference_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PreferenceRecord:
    """Disable a preference."""

    try:
        return container.preference_service.disable_preference(
            preference_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/constraints", response_model=ConstraintRecord)
def create_constraint(
    body: ConstraintRecord,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConstraintRecord:
    """Create one instruction constraint."""

    try:
        return container.constraint_service.create_constraint(
            body.model_copy(update=_context_updates(body, actor_context))
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/constraints", response_model=list[ConstraintRecord])
def list_constraints(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    constraint_type: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ConstraintRecord]:
    """List instruction constraints."""

    try:
        return container.constraint_service.list_constraints(
            _scope(scope, actor_context),
            status=status,
            constraint_type=constraint_type,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/constraints/{constraint_id}/disable", response_model=ConstraintRecord)
def disable_constraint(
    constraint_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConstraintRecord:
    """Disable one instruction constraint."""

    try:
        return container.constraint_service.disable_constraint(
            constraint_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/brain/style-profiles/effective", response_model=StyleProfile | None)
def effective_style_profile(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
) -> StyleProfile | None:
    """Return effective style profile."""

    try:
        return container.style_profile_service.effective_style(
            _scope(scope, actor_context),
            actor_id=actor_id or actor_context.actor_id,
            workspace_id=workspace_id or actor_context.workspace_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/style-profiles", response_model=StyleProfile)
def create_style_profile(
    body: StyleProfileCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> StyleProfile:
    """Create a style profile."""

    try:
        updated = body.model_copy(update=_context_updates(body, actor_context))
        return container.style_profile_service.create_profile(
            updated.to_profile(updated.style_profile_id or f"style-profile-{uuid4().hex}")
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/style-profiles", response_model=list[StyleProfile])
def list_style_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[StyleProfile]:
    """List style profiles."""

    try:
        return container.style_profile_service.list_profiles(
            _scope(scope, actor_context),
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/style-profiles/{style_profile_id}/disable", response_model=StyleProfile)
def disable_style_profile(
    style_profile_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> StyleProfile:
    """Disable a style profile."""

    try:
        return container.style_profile_service.disable_profile(
            style_profile_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _context_updates(body: object, actor_context: ActorContext) -> dict[str, object]:
    updates: dict[str, object] = {}
    if not getattr(body, "owner_scope", None):
        updates["owner_scope"] = actor_context.security_scope or ["workspace:main"]
    if getattr(body, "actor_id", None) is None:
        updates["actor_id"] = actor_context.actor_id
    if getattr(body, "workspace_id", None) is None:
        updates["workspace_id"] = actor_context.workspace_id
    if getattr(body, "created_by", None) is None:
        updates["created_by"] = actor_context.actor_id
    if getattr(body, "trace_id", None) is None:
        updates["trace_id"] = actor_context.trace_id
    return updates


def _normalize_instruction_text(value: str) -> str:
    from aion_brain.instructions.normalizer import normalize_instruction_text

    return normalize_instruction_text(value)


__all__ = ["router"]
