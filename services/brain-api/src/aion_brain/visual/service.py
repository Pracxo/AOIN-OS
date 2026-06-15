"""Policy-gated Visual Brain Projection services."""

from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import (
    BrainMap,
    BrainMapRequest,
    BrainMapSnapshot,
    VisualTelemetryQuery,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.visual.map_builder import BrainMapBuilder
from aion_brain.visual.repository import VisualRepository


class VisualPolicyDenied(RuntimeError):
    """Raised when visual projection policy denies an action."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class VisualTelemetryQueryService:
    """Policy-gated query service over canonical visual telemetry."""

    def __init__(
        self,
        repository: VisualRepository,
        policy_adapter: PolicyAdapter,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> "VisualTelemetryQueryService":
        """Return a request-scoped service."""
        return VisualTelemetryQueryService(self._repository, self._policy_adapter, actor_context)

    def query(self, query: VisualTelemetryQuery) -> list[VisualTelemetryEvent]:
        """Return policy-authorized visual telemetry."""
        self._authorize("visual.telemetry.read", query.trace_id, query.scope)
        return self._repository.query_telemetry(query)

    def get_recent(self, scope: list[str], limit: int = 100) -> list[VisualTelemetryEvent]:
        """Return recent policy-authorized telemetry."""
        return self.query(VisualTelemetryQuery(scope=scope, limit=limit))

    def get_by_trace(self, trace_id: str, scope: list[str]) -> list[VisualTelemetryEvent]:
        """Return policy-authorized telemetry for a trace."""
        return self.query(VisualTelemetryQuery(trace_id=trace_id, scope=scope, limit=1000))

    def authorize_stream(self, trace_id: str | None, scope: list[str]) -> None:
        """Authorize an SSE visual telemetry stream."""
        self._authorize("visual.stream.read", trace_id, scope)

    def _authorize(self, action_type: str, resource_id: str | None, scope: list[str]) -> None:
        request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=resource_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type="visual_telemetry",
            resource_id=resource_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=scope,
            context={},
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(request, self._actor_context)
        )
        if not decision.allow:
            raise VisualPolicyDenied(decision)


class VisualProjectionService:
    """Policy-gated Brain Map and snapshot service."""

    def __init__(
        self,
        builder: BrainMapBuilder,
        repository: VisualRepository,
        policy_adapter: PolicyAdapter,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._builder = builder
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> "VisualProjectionService":
        """Return a request-scoped service."""
        return VisualProjectionService(
            self._builder,
            self._repository,
            self._policy_adapter,
            actor_context,
        )

    def build_map(self, request: BrainMapRequest) -> BrainMap:
        """Build a policy-authorized Brain Map."""
        self._authorize("visual.map.read", request.trace_id, request.scope, "brain_map")
        return self._builder.build(request)

    def create_snapshot(self, request: BrainMapRequest) -> BrainMapSnapshot:
        """Build and persist a policy-authorized snapshot."""
        self._authorize(
            "visual.snapshot.create",
            request.trace_id,
            request.scope,
            "brain_map_snapshot",
        )
        brain_map = self._builder.build(request)
        return self._repository.save_snapshot(
            BrainMapSnapshot(
                snapshot_id=f"snapshot-{uuid4().hex}",
                trace_id=request.trace_id,
                workspace_id=request.workspace_id,
                owner_scope=request.scope,
                map=brain_map,
                node_count=len(brain_map.nodes),
                edge_count=len(brain_map.edges),
                pulse_count=len(brain_map.pulses),
                created_at=None,
            )
        )

    def get_snapshot(self, snapshot_id: str, scope: list[str]) -> BrainMapSnapshot | None:
        """Return a policy-authorized snapshot."""
        self._authorize("visual.snapshot.read", snapshot_id, scope, "brain_map_snapshot")
        snapshot = self._repository.get_snapshot(snapshot_id)
        if snapshot is None or not set(snapshot.owner_scope) & set(scope):
            return None
        return snapshot

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        scope: list[str],
        resource_type: str,
    ) -> None:
        request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=self._actor_context.trace_id or resource_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=scope,
            context={},
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(request, self._actor_context)
        )
        if not decision.allow:
            raise VisualPolicyDenied(decision)
