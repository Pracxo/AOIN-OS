"""Policy simulation service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import PolicySimulationRequest, PolicySimulationResult
from aion_brain.contracts.scopes import ActorContext
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.telemetry import emit_policy_telemetry


class PolicySimulationService:
    """Run side-effect-free policy simulations."""

    def __init__(
        self,
        *,
        repository: PolicyCatalogRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        enricher: PolicyInputEnricher | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._enricher = enricher or PolicyInputEnricher()

    def simulate(
        self,
        request: PolicySimulationRequest,
        actor_context: ActorContext | None = None,
    ) -> PolicySimulationResult:
        """Simulate a policy decision without executing the requested action."""
        self._authorize_simulation(request)
        policy_request = PolicyRequest(
            request_id=f"policy-simulation-{request.simulation_id or uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            action_type=request.action_type,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            risk_level=request.risk_level,
            approval_present=request.approval_present,
            requested_permissions=request.requested_permissions,
            security_scope=request.security_scope,
            context={**request.context, "simulation": True},
        )
        if actor_context is not None:
            policy_request = self._enricher.enrich(policy_request, actor_context)
        decision = self._policy_adapter.authorize(policy_request)
        simulation_id = request.simulation_id or f"policy-simulation-{uuid4().hex}"
        result = PolicySimulationResult(
            simulation_id=simulation_id,
            request=request.model_copy(update={"simulation_id": simulation_id}),
            decision=decision,
            explanation={
                "action_type": request.action_type,
                "resource_type": request.resource_type,
                "requested_permissions": request.requested_permissions,
                "security_scope": policy_request.security_scope,
                "actor_context_present": actor_context is not None,
                "allow": decision.allow,
                "approval_required": decision.approval_required,
                "constraints": decision.constraints,
                "target_action_executed": False,
            },
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_simulation(result)
        self._emit(
            "policy_simulated",
            "policy",
            saved.simulation_id,
            0.6,
            {"action_type": saved.request.action_type, "allow": saved.decision.allow},
        )
        return saved

    def get_simulation(self, simulation_id: str) -> PolicySimulationResult | None:
        """Return one simulation."""
        return self._repository.get_simulation(simulation_id)

    def _authorize_simulation(self, request: PolicySimulationRequest) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"policy.simulate-{request.simulation_id or uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="policy.simulate",
                resource_type="policy_simulation",
                resource_id=request.simulation_id,
                risk_level="medium",
                approval_present=True,
                requested_permissions=["policy.simulate"],
                security_scope=request.security_scope,
                context={"simulated_action_type": request.action_type},
            )
        )
        if not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_policy_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=intensity,
            payload=payload,
        )
