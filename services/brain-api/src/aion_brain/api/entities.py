"""Entity resolver and canonical reference API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.entities import (
    EntityAlias,
    EntityAliasCreateRequest,
    EntityCreateRequest,
    EntityDeleteRequest,
    EntityExtractMentionsRequest,
    EntityMention,
    EntityMentionCreateRequest,
    EntityMergeProposal,
    EntityMergeProposalCreateRequest,
    EntityProposalDecisionRequest,
    EntityQuery,
    EntityQueryResult,
    EntityRecord,
    EntityResolutionRequest,
    EntityResolutionResult,
    EntitySplitProposal,
    EntitySplitProposalCreateRequest,
    ReferenceLink,
    ReferenceLinkCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/entities", tags=["entities"])


@router.post("", response_model=EntityRecord)
def create_entity(
    body: EntityCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EntityRecord:
    """Create one canonical entity reference."""
    try:
        return container.entity_service.create(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/query", response_model=EntityQueryResult)
def query_entities(
    body: EntityQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EntityQueryResult:
    """Query canonical entities."""
    try:
        return container.entity_query_service.query(
            body.model_copy(update={"scope": body.scope or actor_context.security_scope})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/{entity_id}/archive", response_model=EntityRecord)
def archive_entity(
    entity_id: str,
    body: EntityDeleteRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityRecord:
    """Archive one entity."""
    try:
        return container.entity_service.archive(
            entity_id,
            _scope(scope, actor_context),
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id}),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{entity_id}")
def soft_delete_entity(
    entity_id: str,
    body: EntityDeleteRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, str | bool]:
    """Soft-delete one entity."""
    try:
        deleted = container.entity_service.soft_delete(
            entity_id,
            _scope(scope, actor_context),
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id}),
        )
        return {"deleted": True, "entity_id": deleted.entity_id}
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/aliases", response_model=EntityAlias)
def add_alias(
    body: EntityAliasCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityAlias:
    """Add an alias to an entity."""
    try:
        return container.entity_alias_service.add_alias(body, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{entity_id}/aliases", response_model=list[EntityAlias])
def list_aliases(
    entity_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[EntityAlias]:
    """List aliases for an entity."""
    try:
        return container.entity_alias_service.list_aliases(entity_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/aliases/{alias_id}", response_model=EntityAlias)
def delete_alias(
    alias_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityAlias:
    """Soft-delete an alias."""
    try:
        return container.entity_alias_service.delete_alias(alias_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mentions", response_model=EntityMention)
def create_mention(
    body: EntityMentionCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EntityMention:
    """Create one explicit entity mention."""
    try:
        return container.entity_resolver.create_mention(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            ),
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{entity_id}/mentions", response_model=list[EntityMention])
def list_mentions(
    entity_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EntityMention]:
    """List mentions that resolve to an entity."""
    try:
        return container.entity_resolver.list_mentions(
            entity_id,
            _scope(scope, actor_context),
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/extract-mentions", response_model=list[EntityMentionCreateRequest])
def extract_mentions(
    body: EntityExtractMentionsRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[EntityMentionCreateRequest]:
    """Extract entity mentions deterministically."""
    try:
        return container.entity_resolver.extract_mentions(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            ),
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/resolve", response_model=EntityResolutionResult)
def resolve_entities(
    body: EntityResolutionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EntityResolutionResult:
    """Resolve mentions to canonical entity references."""
    try:
        return container.entity_resolver.resolve(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/resolution-runs/{resolution_run_id}", response_model=EntityResolutionResult)
def get_resolution_run(
    resolution_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityResolutionResult:
    """Return a stored entity resolution run."""
    try:
        result = container.entity_resolver.get_resolution_result(
            resolution_run_id,
            _scope(scope, actor_context),
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="entity_resolution_run_not_found")
    return result


@router.post("/references", response_model=ReferenceLink)
def create_reference_link(
    body: ReferenceLinkCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReferenceLink:
    """Create a canonical reference link."""
    try:
        return container.reference_link_service.create_link(
            body.model_copy(update={"trace_id": body.trace_id or actor_context.trace_id}),
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/references", response_model=list[ReferenceLink])
def list_reference_links(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    entity_id: str | None = None,
    concept_id: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ReferenceLink]:
    """List reference links."""
    try:
        return container.reference_link_service.list_links(
            _scope(scope, actor_context),
            entity_id=entity_id,
            concept_id=concept_id,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/merge-proposals", response_model=EntityMergeProposal)
@router.post("/merge/proposals", response_model=EntityMergeProposal, include_in_schema=False)
def propose_merge(
    body: EntityMergeProposalCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityMergeProposal:
    """Propose an entity merge."""
    try:
        return container.entity_merge_service.propose(
            body.model_copy(update={"created_by": body.created_by or actor_context.actor_id}),
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/merge-proposals", response_model=list[EntityMergeProposal])
@router.get("/merge/proposals", response_model=list[EntityMergeProposal], include_in_schema=False)
def list_merge_proposals(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = "proposed",
) -> list[EntityMergeProposal]:
    """List entity merge proposals."""
    try:
        return container.entity_merge_service.list_proposals(
            _scope(scope, actor_context),
            status=status,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/merge-proposals/{proposal_id}/approve", response_model=EntityMergeProposal)
@router.post(
    "/merge/proposals/{proposal_id}/approve",
    response_model=EntityMergeProposal,
    include_in_schema=False,
)
def approve_merge(
    proposal_id: str,
    body: EntityProposalDecisionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityMergeProposal:
    """Approve a merge proposal."""
    try:
        return container.entity_merge_service.approve(
            proposal_id,
            _scope(scope, actor_context),
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id}),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/merge-proposals/{proposal_id}/reject", response_model=EntityMergeProposal)
@router.post(
    "/merge/proposals/{proposal_id}/reject",
    response_model=EntityMergeProposal,
    include_in_schema=False,
)
def reject_merge(
    proposal_id: str,
    body: EntityProposalDecisionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityMergeProposal:
    """Reject a merge proposal."""
    try:
        return container.entity_merge_service.reject(
            proposal_id,
            _scope(scope, actor_context),
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id}),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/split-proposals", response_model=EntitySplitProposal)
@router.post("/split/proposals", response_model=EntitySplitProposal, include_in_schema=False)
def propose_split(
    body: EntitySplitProposalCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntitySplitProposal:
    """Propose an entity split."""
    try:
        return container.entity_split_service.propose(
            body.model_copy(update={"created_by": body.created_by or actor_context.actor_id}),
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/split-proposals", response_model=list[EntitySplitProposal])
@router.get("/split/proposals", response_model=list[EntitySplitProposal], include_in_schema=False)
def list_split_proposals(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = "proposed",
) -> list[EntitySplitProposal]:
    """List entity split proposals."""
    try:
        return container.entity_split_service.list_proposals(
            _scope(scope, actor_context),
            status=status,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/split-proposals/{proposal_id}/approve", response_model=EntitySplitProposal)
@router.post(
    "/split/proposals/{proposal_id}/approve",
    response_model=EntitySplitProposal,
    include_in_schema=False,
)
def approve_split(
    proposal_id: str,
    body: EntityProposalDecisionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntitySplitProposal:
    """Approve a split proposal."""
    try:
        return container.entity_split_service.approve(
            proposal_id,
            _scope(scope, actor_context),
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id}),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/split-proposals/{proposal_id}/reject", response_model=EntitySplitProposal)
@router.post(
    "/split/proposals/{proposal_id}/reject",
    response_model=EntitySplitProposal,
    include_in_schema=False,
)
def reject_split(
    proposal_id: str,
    body: EntityProposalDecisionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntitySplitProposal:
    """Reject a split proposal."""
    try:
        return container.entity_split_service.reject(
            proposal_id,
            _scope(scope, actor_context),
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id}),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{entity_id}", response_model=EntityRecord)
def get_entity(
    entity_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EntityRecord:
    """Return one canonical entity reference."""
    try:
        entity = container.entity_service.get(entity_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if entity is None:
        raise HTTPException(status_code=404, detail="entity_not_found")
    return entity


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope
