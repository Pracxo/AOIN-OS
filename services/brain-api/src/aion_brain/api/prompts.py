"""Prompt Packet Compiler API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.model_inputs import ModelInputManifest
from aion_brain.contracts.prompts import (
    PromptBoundaryCheck,
    PromptCompileRequest,
    PromptCompileResult,
    PromptFragment,
    PromptFragmentCreateRequest,
    PromptInjectionFinding,
    PromptPacket,
    PromptPreview,
    PromptPreviewRequest,
    PromptTemplate,
    PromptTemplateCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/prompts", tags=["prompts"])


class DisableRequest(BaseModel):
    """Disable request body."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="operator_disabled", min_length=1)


class SeedDefaultsRequest(BaseModel):
    """Seed default templates request body."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    dry_run: bool = True


class BoundaryCheckRequest(BaseModel):
    """Boundary check request body for an existing prompt packet."""

    model_config = ConfigDict(extra="forbid")

    prompt_packet_id: str = Field(min_length=1)
    scope: list[str] | None = None


@router.post("/templates", response_model=PromptTemplate)
def create_template(
    body: PromptTemplateCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptTemplate:
    """Create one prompt template."""

    try:
        return container.prompt_template_service.with_actor_context(actor_context).create_template(
            _with_scope(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/templates", response_model=list[PromptTemplate])
def list_templates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = "active",
    template_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PromptTemplate]:
    """List prompt templates."""

    try:
        return container.prompt_template_service.with_actor_context(actor_context).list_templates(
            _scope(scope, actor_context),
            status=status,
            template_type=template_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/templates/{prompt_template_id}", response_model=PromptTemplate)
def get_template(
    prompt_template_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> PromptTemplate:
    """Return one prompt template."""

    try:
        template = container.prompt_template_service.with_actor_context(actor_context).get_template(
            prompt_template_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if template is None:
        raise HTTPException(status_code=404, detail="prompt_template_not_found")
    return template


@router.post("/templates/{prompt_template_id}/disable", response_model=PromptTemplate)
def disable_template(
    prompt_template_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> PromptTemplate:
    """Disable one prompt template."""

    try:
        return container.prompt_template_service.with_actor_context(actor_context).disable_template(
            prompt_template_id,
            scope=_scope(scope, actor_context),
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/templates/seed-defaults")
@router.post("/templates/seed")
def seed_templates(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    body: Annotated[SeedDefaultsRequest | None, Body()] = None,
    scope: Annotated[list[str] | None, Query()] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Seed default generic prompt templates."""

    requested_scope = body.scope if body is not None and body.scope else scope
    requested_dry_run = body.dry_run if body is not None else dry_run
    try:
        return container.prompt_template_service.with_actor_context(actor_context).seed_defaults(
            _scope(requested_scope, actor_context), dry_run=requested_dry_run
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/fragments", response_model=PromptFragment)
def create_fragment(
    body: PromptFragmentCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptFragment:
    """Create one prompt fragment."""

    try:
        return container.prompt_fragment_service.with_actor_context(actor_context).create_fragment(
            _with_scope(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/fragments", response_model=list[PromptFragment])
def list_fragments(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = "active",
    fragment_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PromptFragment]:
    """List prompt fragments."""

    try:
        return container.prompt_fragment_service.with_actor_context(actor_context).list_fragments(
            _scope(scope, actor_context),
            status=status,
            fragment_type=fragment_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/fragments/{prompt_fragment_id}/disable", response_model=PromptFragment)
def disable_fragment(
    prompt_fragment_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> PromptFragment:
    """Disable one prompt fragment."""

    try:
        return container.prompt_fragment_service.with_actor_context(actor_context).disable_fragment(
            prompt_fragment_id,
            scope=_scope(scope, actor_context),
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/compile", response_model=PromptCompileResult)
def compile_prompt(
    body: PromptCompileRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptCompileResult:
    """Compile a governed prompt packet."""

    try:
        return container.prompt_compiler.with_actor_context(actor_context).compile(
            _with_scope(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/packets/{prompt_packet_id}", response_model=PromptPacket)
def get_packet(
    prompt_packet_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> PromptPacket:
    """Return one prompt packet metadata record."""

    try:
        packet = container.prompt_compiler.with_actor_context(actor_context).get_packet(
            prompt_packet_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if packet is None:
        raise HTTPException(status_code=404, detail="prompt_packet_not_found")
    return packet


@router.get("/packets", response_model=list[PromptPacket])
def list_packets(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    trace_id: str | None = None,
    status: str | None = None,
    packet_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[PromptPacket]:
    """List prompt packet metadata records."""

    try:
        return container.prompt_compiler.with_actor_context(actor_context).list_packets(
            _scope(scope, actor_context),
            trace_id=trace_id,
            status=status,
            packet_type=packet_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.delete("/packets/{prompt_packet_id}")
def delete_packet(
    prompt_packet_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    """Soft delete one prompt packet."""

    try:
        return container.prompt_compiler.with_actor_context(actor_context).delete_packet(
            prompt_packet_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/boundary/check", response_model=PromptBoundaryCheck)
def check_boundary(
    body: PromptCompileRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptBoundaryCheck:
    """Compile sections and return only the boundary check."""

    try:
        result = container.prompt_compiler.with_actor_context(actor_context).compile(
            _with_scope(body.model_copy(update={"store_packet": False}), actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if result.boundary_check is None:
        raise HTTPException(status_code=503, detail="prompt_boundary_unavailable")
    return result.boundary_check


@router.post("/boundary-check", response_model=PromptBoundaryCheck)
def check_existing_packet_boundary(
    body: BoundaryCheckRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptBoundaryCheck:
    """Return or rebuild the boundary check for an existing prompt packet."""

    scope = _scope(body.scope, actor_context)
    try:
        packet = container.prompt_compiler.with_actor_context(actor_context).get_packet(
            body.prompt_packet_id,
            scope,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if packet is None:
        raise HTTPException(status_code=404, detail="prompt_packet_not_found")
    if packet.boundary_check_id:
        existing = container.prompt_boundary_checker.get_check(packet.boundary_check_id)
        if existing is not None:
            return existing
    try:
        return container.prompt_boundary_checker.with_actor_context(actor_context).check_packet(
            packet
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/boundary/{boundary_check_id}", response_model=PromptBoundaryCheck)
def get_boundary_check(
    boundary_check_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PromptBoundaryCheck:
    """Return one boundary check."""

    check = container.prompt_boundary_checker.get_check(boundary_check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="prompt_boundary_not_found")
    return check


@router.get("/injection-findings", response_model=list[PromptInjectionFinding])
@router.get("/injections", response_model=list[PromptInjectionFinding])
def list_injections(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    trace_id: str | None = None,
    prompt_packet_id: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[PromptInjectionFinding]:
    """List prompt injection findings."""

    try:
        return container.prompt_boundary_checker.with_actor_context(
            actor_context
        ).list_injection_findings(
            trace_id=trace_id,
            prompt_packet_id=prompt_packet_id,
            severity=severity,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/preview", response_model=PromptPreview)
def preview_prompt(
    body: PromptPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptPreview:
    """Create a safe prompt preview."""

    try:
        return container.prompt_preview_service.with_actor_context(actor_context).preview(
            _with_scope(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/model-input-manifests/{model_input_manifest_id}", response_model=ModelInputManifest)
@router.get("/manifests/{model_input_manifest_id}", response_model=ModelInputManifest)
def get_manifest(
    model_input_manifest_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModelInputManifest:
    """Return one model input manifest."""

    try:
        manifest = container.model_input_manifest_service.with_actor_context(
            actor_context
        ).get_manifest(model_input_manifest_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if manifest is None:
        raise HTTPException(status_code=404, detail="model_input_manifest_not_found")
    return manifest


@router.get("/model-input-manifests", response_model=list[ModelInputManifest])
@router.get("/manifests", response_model=list[ModelInputManifest])
def list_manifests(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    trace_id: str | None = None,
    prompt_packet_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[ModelInputManifest]:
    """List model input manifests."""

    try:
        return container.model_input_manifest_service.with_actor_context(
            actor_context
        ).list_manifests(
            _scope(scope, actor_context),
            trace_id=trace_id,
            prompt_packet_id=prompt_packet_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    if scope:
        return scope
    if actor_context.security_scope:
        return actor_context.security_scope
    if actor_context.workspace_id:
        return [f"workspace:{actor_context.workspace_id}"]
    return ["workspace:main"]


def _with_scope(body: Any, actor_context: ActorContext) -> Any:
    owner_scope = getattr(body, "owner_scope", None)
    if owner_scope:
        return body
    return body.model_copy(update={"owner_scope": _scope(None, actor_context)})


__all__ = ["router"]
