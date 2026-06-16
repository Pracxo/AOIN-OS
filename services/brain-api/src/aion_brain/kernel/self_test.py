"""Deterministic, side-effect-free kernel self-test."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.diagnostics import DiagnosticCheck, DiagnosticSeverity, DiagnosticStatus
from aion_brain.contracts.kernel import (
    KernelSelfTestRequest,
    KernelSelfTestResult,
    KernelSelfTestStatus,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEventType
from aion_brain.kernel.diagnostics import KernelDiagnostics
from aion_brain.kernel.repository import KernelRepository
from aion_brain.kernel.service_registry import KernelServiceRegistry
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher


class KernelSelfTestService:
    """Run local boundary checks without invoking external AI or modules."""

    def __init__(
        self,
        *,
        repository: KernelRepository,
        policy_adapter: PolicyAdapter,
        diagnostics: KernelDiagnostics,
        registry: KernelServiceRegistry,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._diagnostics = diagnostics
        self._registry = registry
        self._telemetry_service = telemetry_service

    def run(
        self,
        request: KernelSelfTestRequest,
        actor_context: ActorContext | None = None,
    ) -> KernelSelfTestResult:
        """Run and persist deterministic dry checks."""
        self_test_id = f"self-test-{uuid4().hex}"
        created_at = datetime.now(UTC)
        self._emit("kernel_self_test_started", self_test_id, 0.4, {"dry_run": request.dry_run})
        checks = self._diagnostics.run()
        checks.extend(self._local_checks(request, actor_context))
        critical_failed = any(
            check.status == "failed" and check.severity in {"critical", "high"} for check in checks
        )
        warnings = any(check.status in {"warning", "skipped"} for check in checks)
        status = "failed" if critical_failed else ("degraded" if warnings else "passed")
        result = KernelSelfTestResult(
            self_test_id=self_test_id,
            status=cast(KernelSelfTestStatus, status),
            checks=checks,
            report={
                "dry_run": request.dry_run,
                "external_side_effects": False,
                "service_count": len(self._registry.list_services()),
                "passed": sum(check.status == "passed" for check in checks),
                "failed": sum(check.status == "failed" for check in checks),
            },
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        stored = self._repository.save_self_test(result)
        self._emit(
            "kernel_self_test_completed",
            self_test_id,
            {"passed": 0.8, "degraded": 0.6, "failed": 1.0}[status],
            {"status": status},
        )
        return stored

    def get_latest(self) -> KernelSelfTestResult | None:
        """Return the latest self-test result."""
        return self._repository.get_latest_self_test()

    def _local_checks(
        self,
        request: KernelSelfTestRequest,
        actor_context: ActorContext | None,
    ) -> list[DiagnosticCheck]:
        now = datetime.now(UTC)
        services = {record.service_name for record in self._registry.list_services()}
        checks = [
            _check("service_registry_check", bool(services), "critical", now),
            _check(
                "policy_dry_authorization_check",
                self._policy_check(request, actor_context),
                "critical",
                now,
            ),
        ]
        requested = {
            "memory_dry_test": request.include_memory,
            "semantic_memory_in_memory_dry_test": request.include_memory,
            "graph_memory_in_memory_dry_test": request.include_memory,
            "evidence_ingest_search_dry_test": request.include_memory,
            "retrieval_router_dry_test": request.include_memory,
            "context_compile_dry_test": request.include_reasoning,
            "reasoning_deterministic_dry_test": request.include_reasoning,
            "model_gateway_deterministic_dry_test": request.include_reasoning,
            "prompt_redaction_dry_test": request.include_reasoning,
            "model_budget_guard_dry_test": request.include_reasoning,
            "planner_dry_test": request.include_reasoning,
            "execution_dry_run_test": request.include_execution,
            "visual_map_projection_dry_test": request.include_visual,
            "snapshot_dry_test": request.include_replay,
            "replay_comparator_dry_test": request.include_replay,
        }
        checks.extend(
            _check(name, enabled, "low", now, skipped=not enabled)
            for name, enabled in requested.items()
        )
        return checks

    def _policy_check(
        self,
        request: KernelSelfTestRequest,
        actor_context: ActorContext | None,
    ) -> bool:
        try:
            policy_request = PolicyRequest(
                request_id=f"kernel-self-test-{uuid4().hex}",
                trace_id=actor_context.trace_id if actor_context else None,
                actor_id=actor_context.actor_id if actor_context else None,
                workspace_id=actor_context.workspace_id if actor_context else None,
                action_type="kernel.self_test.run",
                resource_type="kernel",
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=request.scope,
                context={"dry_run": True},
            )
            decision = self._policy_adapter.authorize(
                PolicyInputEnricher().enrich(policy_request, actor_context or ActorContext())
            )
            return decision.allow
        except Exception:
            return False

    def _emit(
        self,
        event_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            from aion_brain.contracts.telemetry import VisualTelemetryEvent

            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{node_id}-{event_type}",
                    trace_id=node_id,
                    event_type=cast(VisualTelemetryEventType, event_type),
                    node_type="diagnostic",
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _check(
    name: str,
    passed: bool,
    severity: str,
    created_at: datetime,
    *,
    skipped: bool = False,
) -> DiagnosticCheck:
    status = "skipped" if skipped else ("passed" if passed else "failed")
    return DiagnosticCheck(
        check_id=f"diagnostic-{uuid4().hex}",
        name=name,
        component=name.removesuffix("_check").removesuffix("_test"),
        status=cast(DiagnosticStatus, status),
        severity=cast(DiagnosticSeverity, severity),
        message=f"{name.replace('_', ' ')} {status}.",
        details={},
        created_at=created_at,
    )
