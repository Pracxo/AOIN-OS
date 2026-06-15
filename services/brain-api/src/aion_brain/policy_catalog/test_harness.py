"""Deterministic policy test harness."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import (
    PolicySimulationRequest,
    PolicyTestCase,
    PolicyTestRun,
    PolicyTestRunRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.simulation import PolicySimulationService
from aion_brain.policy_catalog.telemetry import emit_policy_telemetry


class PolicyTestHarness:
    """Create and run policy tests without mutating target resources."""

    def __init__(
        self,
        *,
        repository: PolicyCatalogRepository,
        policy_adapter: PolicyAdapter,
        simulation_service: PolicySimulationService,
        telemetry_service: object | None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._simulation_service = simulation_service
        self._telemetry_service = telemetry_service

    def create_test_case(self, test_case: PolicyTestCase) -> PolicyTestCase:
        """Create or update one policy test case."""
        self._authorize(
            "policy.test_case.create",
            "policy_test_case",
            test_case.policy_test_case_id,
        )
        return self._repository.save_test_case(test_case)

    def list_test_cases(
        self,
        status: str | None = None,
        tags: list[str] | None = None,
    ) -> list[PolicyTestCase]:
        """List test cases."""
        self._authorize("policy.test_case.read", "policy_test_case", None, risk_level="low")
        return self._repository.list_test_cases(status=status, tags=tags or [])

    def run_tests(
        self,
        request: PolicyTestRunRequest,
        actor_context: ActorContext | None = None,
    ) -> PolicyTestRun:
        """Run selected policy tests through simulation."""
        self._authorize("policy.test.run", "policy_test_run", request.policy_test_run_id)
        run_id = request.policy_test_run_id or f"policy-test-run-{uuid4().hex}"
        self._emit("policy_test_run_started", "test", run_id, 0.5, {})
        cases = self._select_cases(request)
        results = [
            self._run_case(test_case, actor_context)
            for test_case in cases
        ]
        passed_count = sum(result["passed"] is True for result in results)
        failed_count = sum(result["passed"] is False for result in results)
        warning_count = 0
        status = "failed" if failed_count else "passed"
        run = PolicyTestRun(
            policy_test_run_id=run_id,
            status=cast(Any, status),
            total_count=len(results),
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=warning_count,
            results=results,
            report={"dry_run": request.dry_run, "target_action_executed": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_test_run(run)
        self._emit(
            "policy_test_run_completed",
            "test",
            saved.policy_test_run_id,
            0.8 if saved.status == "passed" else 1.0,
            {"status": saved.status, "total_count": saved.total_count},
        )
        return saved

    def _select_cases(self, request: PolicyTestRunRequest) -> list[PolicyTestCase]:
        status = None if request.include_disabled else "active"
        cases = self._repository.list_test_cases(status=status, tags=request.tags)
        if not request.test_case_ids:
            return cases
        selected = set(request.test_case_ids)
        return [case for case in cases if case.policy_test_case_id in selected]

    def _run_case(
        self,
        test_case: PolicyTestCase,
        actor_context: ActorContext | None,
    ) -> dict[str, Any]:
        simulation = self._simulation_service.simulate(
            PolicySimulationRequest.model_validate(test_case.input),
            actor_context,
        )
        expected = test_case.expected
        checks = {
            "allow": (
                expected.get("allow") == simulation.decision.allow
                if "allow" in expected
                else True
            ),
            "approval_required": (
                expected.get("approval_required") == simulation.decision.approval_required
                if "approval_required" in expected
                else True
            ),
            "audit_level": (
                expected.get("audit_level") == simulation.decision.audit_level
                if "audit_level" in expected
                else True
            ),
            "reason_contains": (
                str(expected.get("reason_contains")) in simulation.decision.reason
                if "reason_contains" in expected
                else True
            ),
        }
        passed = all(checks.values())
        return {
            "policy_test_case_id": test_case.policy_test_case_id,
            "name": test_case.name,
            "passed": passed,
            "checks": checks,
            "decision": simulation.decision.model_dump(mode="json"),
            "simulation_id": simulation.simulation_id,
        }

    def _authorize(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        *,
        risk_level: str = "medium",
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=["workspace:main"],
                context={},
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
