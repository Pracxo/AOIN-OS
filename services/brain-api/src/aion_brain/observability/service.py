"""Policy-gated observability service."""

from uuid import uuid4

from aion_brain.contracts.observability import ObservabilityEvent, ObservabilitySummary
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.observability.base import ObservabilityAdapter
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.visual.service import VisualPolicyDenied


class ObservabilityService:
    """Apply policy before local observability access."""

    def __init__(
        self,
        adapter: ObservabilityAdapter,
        policy_adapter: PolicyAdapter,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._adapter = adapter
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> "ObservabilityService":
        """Return a request-scoped service."""
        return ObservabilityService(self._adapter, self._policy_adapter, actor_context)

    def record_event(self, event: ObservabilityEvent) -> ObservabilityEvent:
        """Policy-gate and record an observability event."""
        self._authorize("observability.event.create", event.trace_id, [])
        return self._adapter.record_event(event)

    def summarize(self, scope: list[str]) -> ObservabilitySummary:
        """Policy-gate and summarize local observability."""
        self._authorize("observability.read", None, scope)
        return self._adapter.summarize(scope)

    def _authorize(self, action_type: str, trace_id: str | None, scope: list[str]) -> None:
        request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type="observability",
            resource_id=trace_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=scope or self._actor_context.security_scope,
            context={},
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(request, self._actor_context)
        )
        if not decision.allow:
            raise VisualPolicyDenied(decision)
