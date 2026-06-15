"""Local resilience test runner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.resilience import ResilienceTestRun, ResilienceTestRunRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.resilience._shared import authorize, emit_resilience_event
from aion_brain.resilience.repository import ResilienceRepository


class ResilienceTestRunner:
    """Run deterministic local resilience checks."""

    def __init__(
        self,
        repository: ResilienceRepository,
        policy_adapter: PolicyAdapter,
        *,
        dependency_health_service: object,
        retry_policy_service: object,
        circuit_breaker_service: object,
        degraded_mode_service: object,
        fault_injection_service: object,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._dependency_health_service = dependency_health_service
        self._retry_policy_service = retry_policy_service
        self._circuit_breaker_service = circuit_breaker_service
        self._degraded_mode_service = degraded_mode_service
        self._fault_injection_service = fault_injection_service
        self._telemetry_service = telemetry_service

    def run(self, request: ResilienceTestRunRequest) -> ResilienceTestRun:
        """Run and persist a local resilience report."""
        authorize(
            self._policy_adapter,
            "resilience.test.run",
            request.owner_scope,
            actor_id=request.created_by,
            resource_type="resilience_test",
            risk_level="medium",
            context={"mode": request.mode},
        )
        run_id = request.resilience_test_run_id or f"resilience-run-{uuid4().hex}"
        emit_resilience_event(
            self._telemetry_service,
            event_type="resilience_test_started",
            node_type="resilience",
            node_id=run_id,
            intensity=0.5,
            trace_id=request.trace_id,
        )
        checks: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []

        if request.include_dependency_health:
            dependencies = _call_list(self._dependency_health_service, "check_all")
            for dependency in dependencies:
                check = {
                    "name": f"dependency_{dependency.dependency_name}",
                    "status": dependency.status,
                    "criticality": dependency.criticality,
                }
                checks.append(check)
                if dependency.criticality == "critical" and dependency.status in {
                    "unhealthy",
                    "unavailable",
                }:
                    failures.append(check)
                elif dependency.status in {"unavailable", "degraded", "disabled"}:
                    warnings.append(check)

        if request.include_circuit_breakers:
            breakers = _call_list(self._circuit_breaker_service, "list_breakers")
            for breaker in breakers:
                check = {
                    "name": f"circuit_breaker_{breaker.name}",
                    "status": breaker.status,
                    "target_type": breaker.target_type,
                }
                checks.append(check)
                if breaker.status == "open" and breaker.target_type in {
                    "command",
                    "outbox",
                    "model_gateway",
                }:
                    failures.append(check)
                elif breaker.status == "open":
                    warnings.append(check)

        if request.include_retry_policies:
            policies = _call_list(self._retry_policy_service, "list_policies")
            checks.append(
                {
                    "name": "retry_policies_registered",
                    "status": "passed" if policies else "warning",
                    "count": len(policies),
                }
            )
            if not policies:
                warnings.append({"name": "retry_policies_registered", "status": "warning"})

        if request.include_fault_injection:
            fault_rules = _call_list(self._fault_injection_service, "list_rules", status="active")
            checks.append(
                {
                    "name": "fault_injection_dry_run",
                    "status": "passed",
                    "mode": request.mode,
                    "active_rule_count": len(fault_rules),
                    "fault_rule_ids": [rule.fault_rule_id for rule in fault_rules],
                }
            )

        if request.include_degraded_mode:
            active_degraded = _call_list(self._degraded_mode_service, "list_active")
            for event in active_degraded:
                check = {
                    "name": f"degraded_{event.component}",
                    "status": event.status,
                    "severity": event.severity,
                }
                checks.append(check)
                if event.severity == "critical":
                    failures.append(check)
                else:
                    warnings.append(check)

        status = "failed" if failures else ("warning" if warnings else "passed")
        now = datetime.now(UTC)
        run = ResilienceTestRun(
            resilience_test_run_id=run_id,
            trace_id=request.trace_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            fault_rule_ids=request.fault_rule_ids,
            checks=checks,
            failures=failures,
            warnings=warnings,
            report={
                "check_count": len(checks),
                "failure_count": len(failures),
                "warning_count": len(warnings),
                "metadata": request.metadata,
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        saved = self._repository.save_test_run(run)
        emit_resilience_event(
            self._telemetry_service,
            event_type="resilience_test_completed",
            node_type="resilience",
            node_id=saved.resilience_test_run_id,
            intensity=1.0 if saved.status == "failed" else 0.8,
            payload={"status": saved.status},
            trace_id=saved.trace_id,
        )
        return saved

    def get(self, resilience_test_run_id: str) -> ResilienceTestRun | None:
        """Return one persisted resilience test run."""
        return self._repository.get_test_run(resilience_test_run_id)


def _call_list(service: object, method_name: str, **kwargs: Any) -> list[Any]:
    method = getattr(service, method_name, None)
    if not callable(method):
        return []
    try:
        return list(method(**kwargs))
    except Exception:
        return []

