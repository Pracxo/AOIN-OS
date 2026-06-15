"""Resilience control-plane API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.resilience import (
    CircuitBreaker,
    DegradedModeEvent,
    DependencyHealth,
    FaultInjectionRule,
    ResilienceDryRunRequest,
    ResilienceStatus,
    ResilienceStatusUpdateRequest,
    ResilienceTestRun,
    ResilienceTestRunRequest,
    RetryPolicy,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.resilience._shared import authorize
from aion_brain.resilience.circuit_breakers import CircuitBreakerService
from aion_brain.resilience.degraded_mode import DegradedModeService
from aion_brain.resilience.dependency_health import DependencyHealthService
from aion_brain.resilience.fault_injection import FaultInjectionService
from aion_brain.resilience.retry_policies import RetryPolicyService
from aion_brain.resilience.test_runner import ResilienceTestRunner

router = APIRouter(prefix="/brain/resilience", tags=["resilience"])


def get_dependency_health_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> DependencyHealthService:
    return container.dependency_health_service


def get_retry_policy_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> RetryPolicyService:
    return container.retry_policy_service


def get_circuit_breaker_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> CircuitBreakerService:
    return container.circuit_breaker_service


def get_degraded_mode_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> DegradedModeService:
    return container.degraded_mode_service


def get_fault_injection_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> FaultInjectionService:
    return container.fault_injection_service


def get_resilience_test_runner(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ResilienceTestRunner:
    return container.resilience_test_runner


@router.get("/status", response_model=ResilienceStatus)
def resilience_status(
    service: Annotated[DegradedModeService, Depends(get_degraded_mode_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResilienceStatus:
    """Return combined resilience status."""
    _authorize(container, actor_context, "resilience.status.read")
    return service.status()


@router.post("/dependencies/check", response_model=list[DependencyHealth])
def check_dependencies(
    service: Annotated[DependencyHealthService, Depends(get_dependency_health_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[DependencyHealth]:
    """Run dependency health checks."""
    _authorize(container, actor_context, "resilience.dependency.check", risk_level="medium")
    return service.check_all()


@router.get("/dependencies", response_model=list[DependencyHealth])
def list_dependencies(
    service: Annotated[DependencyHealthService, Depends(get_dependency_health_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    dependency_type: str | None = None,
    component: str | None = None,
) -> list[DependencyHealth]:
    """List latest dependency health records."""
    _authorize(container, actor_context, "resilience.dependency.read")
    return service.list_latest(dependency_type=dependency_type, component=component)


@router.post("/retry-policies", response_model=RetryPolicy)
def create_retry_policy(
    body: RetryPolicy,
    service: Annotated[RetryPolicyService, Depends(get_retry_policy_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RetryPolicy:
    """Create one retry policy."""
    return service.create_policy(
        body.model_copy(
            update={
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
    )


@router.get("/retry-policies", response_model=list[RetryPolicy])
def list_retry_policies(
    service: Annotated[RetryPolicyService, Depends(get_retry_policy_service)],
    status: str | None = None,
    target_type: str | None = None,
) -> list[RetryPolicy]:
    """List retry policies."""
    return service.list_policies(status=status, target_type=target_type)


@router.post("/retry-policies/seed-defaults")
def seed_retry_policies(
    body: ResilienceDryRunRequest,
    service: Annotated[RetryPolicyService, Depends(get_retry_policy_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed or preview default retry policies."""
    _authorize(
        container,
        actor_context,
        "resilience.retry_policy.read" if body.dry_run else "resilience.retry_policy.create",
        risk_level="low" if body.dry_run else "medium",
    )
    return service.seed_defaults(dry_run=body.dry_run)


@router.post("/circuit-breakers", response_model=CircuitBreaker)
def create_circuit_breaker(
    body: CircuitBreaker,
    service: Annotated[CircuitBreakerService, Depends(get_circuit_breaker_service)],
) -> CircuitBreaker:
    """Create one circuit breaker."""
    return service.create_breaker(body)


@router.get("/circuit-breakers", response_model=list[CircuitBreaker])
def list_circuit_breakers(
    service: Annotated[CircuitBreakerService, Depends(get_circuit_breaker_service)],
    status: str | None = None,
    target_type: str | None = None,
) -> list[CircuitBreaker]:
    """List circuit breakers."""
    return service.list_breakers(status=status, target_type=target_type)


@router.post("/circuit-breakers/{name}/reset", response_model=CircuitBreaker)
def reset_circuit_breaker(
    name: str,
    body: ResilienceStatusUpdateRequest,
    service: Annotated[CircuitBreakerService, Depends(get_circuit_breaker_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CircuitBreaker:
    """Reset one circuit breaker."""
    return service.reset(name, body.actor_id or actor_context.actor_id, body.reason)


@router.get("/degraded", response_model=list[DegradedModeEvent])
def list_degraded(
    service: Annotated[DegradedModeService, Depends(get_degraded_mode_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    component: str | None = None,
) -> list[DegradedModeEvent]:
    """List active degraded mode records."""
    _authorize(container, actor_context, "resilience.degraded.read")
    return service.list_active(component=component)


@router.post("/degraded/{degraded_event_id}/resolve", response_model=DegradedModeEvent)
def resolve_degraded(
    degraded_event_id: str,
    body: ResilienceStatusUpdateRequest,
    service: Annotated[DegradedModeService, Depends(get_degraded_mode_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DegradedModeEvent:
    """Resolve one degraded mode record."""
    _authorize(
        container,
        actor_context,
        "resilience.degraded.resolve",
        risk_level="medium",
        resource_type="degraded_mode",
        resource_id=degraded_event_id,
    )
    return service.resolve(degraded_event_id, body.actor_id or actor_context.actor_id, body.reason)


@router.post("/fault-rules", response_model=FaultInjectionRule)
def create_fault_rule(
    body: FaultInjectionRule,
    service: Annotated[FaultInjectionService, Depends(get_fault_injection_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FaultInjectionRule:
    """Create one fault injection rule."""
    return service.create_rule(
        body.model_copy(
            update={
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
    )


@router.get("/fault-rules", response_model=list[FaultInjectionRule])
def list_fault_rules(
    service: Annotated[FaultInjectionService, Depends(get_fault_injection_service)],
    status: str | None = None,
    target_type: str | None = None,
) -> list[FaultInjectionRule]:
    """List fault injection rules."""
    return service.list_rules(status=status, target_type=target_type)


@router.post("/fault-rules/{fault_rule_id}/disable", response_model=FaultInjectionRule)
def disable_fault_rule(
    fault_rule_id: str,
    body: ResilienceStatusUpdateRequest,
    service: Annotated[FaultInjectionService, Depends(get_fault_injection_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FaultInjectionRule:
    """Disable one fault injection rule."""
    return service.disable_rule(fault_rule_id, body.actor_id or actor_context.actor_id, body.reason)


@router.post("/test/run", response_model=ResilienceTestRun)
def run_resilience_test(
    body: ResilienceTestRunRequest,
    service: Annotated[ResilienceTestRunner, Depends(get_resilience_test_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResilienceTestRun:
    """Run a local resilience test."""
    return service.run(
        body.model_copy(
            update={
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
    )


@router.get("/test-runs/{resilience_test_run_id}", response_model=ResilienceTestRun)
def get_resilience_test_run(
    resilience_test_run_id: str,
    service: Annotated[ResilienceTestRunner, Depends(get_resilience_test_runner)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResilienceTestRun:
    """Return one resilience test run."""
    _authorize(
        container,
        actor_context,
        "resilience.test.read",
        resource_type="resilience_test",
        resource_id=resilience_test_run_id,
    )
    run = service.get(resilience_test_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="resilience_test_run_not_found")
    return run


def _authorize(
    container: KernelContainer,
    actor_context: ActorContext,
    action_type: str,
    *,
    risk_level: str = "low",
    resource_type: str = "resilience",
    resource_id: str | None = None,
) -> None:
    authorize(
        container.policy_adapter,
        action_type,
        actor_context.security_scope,
        actor_id=actor_context.actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        risk_level=risk_level,
    )
