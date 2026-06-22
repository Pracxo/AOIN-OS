"""Policy-gated prompt fragment service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.prompts import PromptFragment, PromptFragmentCreateRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.prompts.audit import record_prompt_audit
from aion_brain.prompts.hash import hash_prompt_text


class PromptFragmentService:
    """Create, list, and disable reusable prompt fragments."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> PromptFragmentService:
        return PromptFragmentService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            actor_context=actor_context,
        )

    def create_fragment(self, request: PromptFragmentCreateRequest) -> PromptFragment:
        """Create one prompt fragment after policy authorization."""

        authorize(
            self._policy_adapter,
            action_type="prompt.fragment.create",
            resource_type="prompt_fragment",
            resource_id=request.prompt_fragment_id or request.name,
            scope=request.owner_scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
            context={"fragment_type": request.fragment_type},
        )
        now = datetime.now(UTC)
        fragment = PromptFragment(
            prompt_fragment_id=request.prompt_fragment_id or f"prompt-fragment-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active",
            fragment_type=request.fragment_type,
            content=request.content,
            content_hash=hash_prompt_text(request.content),
            owner_scope=request.owner_scope,
            constraints=request.constraints,
            metadata=request.metadata,
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        save = getattr(self._repository, "save_fragment", None)
        stored = save(fragment) if callable(save) else fragment
        emit_telemetry(
            self._telemetry_service,
            event_type="prompt_fragment_created",
            node_type="prompt_fragment",
            node_id=stored.prompt_fragment_id,
            trace_id=self._actor_context.trace_id,
            intensity=0.5,
            payload={"fragment_type": stored.fragment_type, "owner_scope": stored.owner_scope},
        )
        record_prompt_audit(
            self._audit_sink,
            action_type="prompt.fragment.create",
            resource_type="prompt_fragment",
            resource_id=stored.prompt_fragment_id,
            event_type="prompt_fragment_created",
            trace_id=self._actor_context.trace_id,
            actor_context=self._actor_context,
            payload={"fragment_type": stored.fragment_type, "name": stored.name},
        )
        return stored

    def list_fragments(
        self,
        scope: list[str],
        *,
        status: str | None = "active",
        fragment_type: str | None = None,
        limit: int = 100,
    ) -> list[PromptFragment]:
        """List visible fragments."""

        authorize(
            self._policy_adapter,
            action_type="prompt.fragment.read",
            resource_type="prompt_fragment",
            resource_id=None,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_fragments = getattr(self._repository, "list_fragments", None)
        if not callable(list_fragments):
            return []
        result = list_fragments(scope, status=status, fragment_type=fragment_type, limit=limit)
        return [fragment for fragment in result if isinstance(fragment, PromptFragment)]

    def disable_fragment(
        self,
        prompt_fragment_id: str,
        *,
        scope: list[str],
        reason: str,
    ) -> PromptFragment:
        """Disable one fragment."""

        authorize(
            self._policy_adapter,
            action_type="prompt.fragment.update",
            resource_type="prompt_fragment",
            resource_id=prompt_fragment_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
            context={"reason": reason},
        )
        disable = getattr(self._repository, "disable_fragment", None)
        fragment = (
            disable(prompt_fragment_id, reason=reason, actor_id=self._actor_context.actor_id)
            if callable(disable)
            else None
        )
        if not isinstance(fragment, PromptFragment):
            raise ValueError("prompt_fragment_not_found")
        return fragment


__all__ = ["PromptFragmentService"]
