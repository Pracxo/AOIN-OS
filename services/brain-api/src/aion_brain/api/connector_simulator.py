"""Synthetic connector dry-run simulator API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.connector_simulator import (
    ConnectorPolicyReadinessRequest,
    ConnectorPolicyReadinessResult,
    ConnectorReplayFixture,
    ConnectorSimulationRequest,
    ConnectorSimulationResult,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/connector-simulator", tags=["connector-simulator"])


@router.post("/simulate", response_model=ConnectorSimulationResult)
def simulate_connector(
    body: ConnectorSimulationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorSimulationResult:
    """Run one deterministic local synthetic connector simulation."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_simulator.simulate",
        resolved_scope,
        actor_context,
        resource_type="connector_simulation",
        risk_level="medium",
        context={**_safe_context(), "simulation_type": "dry_run"},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_dry_run_simulator.simulate(request)


@router.post("/replay", response_model=ConnectorSimulationResult)
def replay_connector_fixture(
    body: ConnectorReplayFixture,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorSimulationResult:
    """Replay one local synthetic fixture without external calls."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_simulator.replay",
        resolved_scope,
        actor_context,
        resource_type="connector_replay_fixture",
        risk_level="medium",
        context={**_safe_context(), "fixture_type": body.fixture_type},
    )
    fixture = body.model_copy(update={"owner_scope": resolved_scope})
    return container.connector_replay_service.replay(fixture)


@router.post("/policy-readiness", response_model=ConnectorPolicyReadinessResult)
def connector_policy_readiness(
    body: ConnectorPolicyReadinessRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorPolicyReadinessResult:
    """Evaluate connector simulator policy readiness without runtime approval."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_simulator.policy_readiness",
        resolved_scope,
        actor_context,
        resource_type="connector_policy_readiness",
        risk_level="medium",
        context={**_safe_context(), "policy_readiness_is_approval": False},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_policy_readiness_service.check(request)


@router.get("/status", response_model=dict[str, Any])
def connector_simulator_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Return connector simulator status without runtime activation."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_simulator.status.read",
        resolved_scope,
        actor_context,
        resource_type="connector_simulator_status",
        context=_safe_context(),
    )
    return container.connector_simulator_query_service.status(resolved_scope)


@router.post("/query", response_model=dict[str, Any])
def query_connector_simulator(
    body: dict[str, Any],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Return a deterministic stateless simulator query summary."""

    requested_scope = body.get("owner_scope")
    resolved_scope = (
        [str(item) for item in requested_scope if str(item).strip()]
        if isinstance(requested_scope, list)
        else _scope(None, actor_context)
    )
    _authorize(
        container.policy_adapter,
        "connector_simulator.query",
        resolved_scope,
        actor_context,
        resource_type="connector_simulator_query",
        context=_safe_context(),
    )
    return container.connector_simulator_query_service.query(body, resolved_scope)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "read_only": True,
        "synthetic_only": True,
        "dry_run_only": True,
        "connector_runtime_enabled": False,
        "connector_external_calls_enabled": False,
        "connector_credentials_enabled": False,
        "connector_token_storage_enabled": False,
        "connector_activation_enabled": False,
        "connector_route_registration_enabled": False,
        "external_calls_made": False,
        "credentials_used": False,
        "tokens_used": False,
        "activation_allowed": False,
        "route_registration_allowed": False,
        "write_allowed": False,
        "execute_allowed": False,
        "trusted": False,
    }


def _authorize(
    policy_adapter: object,
    action_type: str,
    scope: list[str],
    actor_context: ActorContext,
    *,
    resource_type: str,
    risk_level: str = "low",
    context: dict[str, Any] | None = None,
) -> None:
    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        raise AIONPolicyDeniedException("policy_adapter_unavailable")
    decision = authorize(
        PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=None,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context={
                "actor_context": actor_context.model_dump(),
                **(context or {}),
            },
        )
    )
    if not decision.allow:
        raise AIONPolicyDeniedException(decision.reason)


__all__ = ["router"]
