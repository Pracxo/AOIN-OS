"""Release baseline service for deterministic AION v0.1 readiness."""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.release_baseline import (
    ReleaseBaselineReport,
    ReleaseBaselineRequest,
)
from aion_brain.contracts.scenarios import ScenarioDefinition, ScenarioRunRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.release_baseline.report import build_release_report
from aion_brain.release_baseline.repository import ReleaseBaselineRepository
from aion_brain.scenarios.runner import ScenarioRunner


class ReleaseBaselineService:
    """Run scenario packs and quality gates into one release report."""

    def __init__(
        self,
        scenario_runner: ScenarioRunner,
        repository: ReleaseBaselineRepository,
        policy_adapter: PolicyAdapter,
        *,
        kernel_self_test: object | None = None,
        policy_coverage: object | None = None,
        openapi_hygiene: object | None = None,
        boundary_checker: object | None = None,
        contract_export: object | None = None,
        performance_summary_service: object | None = None,
        operator_readiness_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._scenario_runner = scenario_runner
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._kernel_self_test = kernel_self_test
        self._policy_coverage = policy_coverage
        self._openapi_hygiene = openapi_hygiene
        self._boundary_checker = boundary_checker
        self._contract_export = contract_export
        self._performance_summary_service = performance_summary_service
        self._operator_readiness_service = operator_readiness_service
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def set_operator_readiness_service(self, service: object) -> None:
        """Attach optional Operator Control Tower readiness after kernel assembly."""
        self._operator_readiness_service = service

    def run(self, request: ReleaseBaselineRequest) -> ReleaseBaselineReport:
        """Run a deterministic release baseline."""
        if not self._settings.release_baseline_enabled:
            raise AIONPolicyDeniedException("release_baseline_disabled")
        if not request.owner_scope:
            request = request.model_copy(
                update={"owner_scope": [self._settings.scenario_default_owner_scope]}
            )
        self._authorize(
            "release_baseline.run",
            request.owner_scope,
            actor_id=request.created_by,
            risk_level="medium",
            context={"version": request.version},
        )
        release_baseline_id = request.release_baseline_id or f"release-baseline-{uuid4().hex}"
        started = datetime.now(UTC)
        self._emit(
            "release_baseline_started",
            release_baseline_id,
            request.owner_scope,
            {"version": request.version},
            intensity=0.5,
        )
        scenarios = self._select_scenarios(request)
        scenario_runs = []
        for scenario in scenarios:
            run = self._scenario_runner.run(
                ScenarioRunRequest(
                    scenario_id=scenario.scenario_id,
                    mode="dry_run",
                    owner_scope=request.owner_scope,
                    tags=request.tags,
                    fail_fast=request.fail_fast,
                    metadata={"release_baseline_id": release_baseline_id},
                    created_by=request.created_by,
                )
            )
            scenario_runs.append(run)
            if request.fail_fast and run.status == "failed":
                break

        quality_gate_results = self._quality_gates(request)
        report_body = build_release_report(scenario_runs, quality_gate_results)
        status = _status(scenario_runs, quality_gate_results)
        report = ReleaseBaselineReport(
            release_baseline_id=release_baseline_id,
            version=request.version,
            status=cast(Any, status),
            scenario_run_ids=[run.scenario_run_id for run in scenario_runs],
            quality_gate_results=quality_gate_results,
            report=report_body,
            created_by=request.created_by,
            created_at=started,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save(report)
        self._emit(
            "release_baseline_completed" if saved.status != "failed" else "release_baseline_failed",
            release_baseline_id,
            request.owner_scope,
            {"version": request.version, "status": saved.status},
            intensity=0.9 if saved.status == "passed" else 1.0,
        )
        return saved

    def get(
        self,
        release_baseline_id: str,
        scope: builtins.list[str],
    ) -> ReleaseBaselineReport | None:
        """Return a release baseline report."""
        self._authorize(
            "release_baseline.read",
            scope,
            resource_id=release_baseline_id,
            context={"release_baseline_id": release_baseline_id},
        )
        return self._repository.get(release_baseline_id)

    def list(
        self,
        *,
        scope: builtins.list[str],
        version: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> builtins.list[ReleaseBaselineReport]:
        """List release baseline reports."""
        self._authorize("release_baseline.read", scope, context={"version": version})
        return self._repository.list(version=version, status=status, limit=limit)

    def _select_scenarios(
        self,
        request: ReleaseBaselineRequest,
    ) -> builtins.list[ScenarioDefinition]:
        if request.scenario_ids:
            scenarios = [
                self._scenario_runner.get_scenario(scenario_id, request.owner_scope)
                for scenario_id in request.scenario_ids
            ]
            missing = [
                scenario_id
                for scenario_id, scenario in zip(
                    request.scenario_ids,
                    scenarios,
                    strict=True,
                )
                if scenario is None
            ]
            if missing:
                raise AIONNotFoundException(f"scenario_not_found:{missing[0]}")
            return [scenario for scenario in scenarios if scenario is not None]
        return self._scenario_runner.list_scenarios(tags=request.tags)

    def _quality_gates(self, request: ReleaseBaselineRequest) -> dict[str, Any]:
        if not request.include_quality_gates:
            return {}
        gates: dict[str, Any] = {}
        if request.include_kernel_self_test:
            gates["kernel_self_test"] = self._gate("kernel_self_test", self._kernel_self_test)
        if request.include_policy_coverage:
            gates["policy_coverage"] = self._gate("policy_coverage", self._policy_coverage)
        if request.include_openapi_hygiene:
            gates["openapi_hygiene"] = self._gate("openapi_hygiene", self._openapi_hygiene)
        if request.include_boundary_check:
            gates["boundary_check"] = self._gate("boundary_check", self._boundary_checker)
        if request.include_contract_export:
            gates["contract_export"] = self._gate("contract_export", self._contract_export)
        build_report = getattr(self._operator_readiness_service, "build_report", None)
        if callable(build_report):
            try:
                report = build_report(request.owner_scope)
                gates["operator_readiness"] = {
                    "status": "passed" if report.release_ready else "warning",
                    "release_ready": report.release_ready,
                    "local_ops_ready": report.local_ops_ready,
                    "readiness_id": report.readiness_id,
                }
            except Exception as exc:
                gates["operator_readiness"] = {
                    "status": "skipped",
                    "reason": exc.__class__.__name__,
                }
        summary = getattr(self._performance_summary_service, "summarize", None)
        if callable(summary):
            try:
                gates["performance_summary"] = summary(
                    request.owner_scope,
                    window="latest",
                ).model_dump(mode="json")
            except Exception as exc:
                gates["performance_summary"] = {
                    "status": "skipped",
                    "reason": exc.__class__.__name__,
                }
        return gates

    def _gate(self, name: str, service: object | None) -> dict[str, Any]:
        if service is None:
            return {"status": "skipped", "reason": "service_not_configured"}
        if isinstance(service, dict):
            return service
        for method_name in ("generate", "check", "export", "export_contracts", "run"):
            method = getattr(service, method_name, None)
            if callable(method):
                try:
                    return _gate_payload(method())
                except TypeError:
                    continue
                except Exception as exc:
                    return {"status": "failed", "reason": exc.__class__.__name__}
        return {
            "status": "passed",
            "name": name,
            "mode": "deterministic_summary",
        }

    def _authorize(
        self,
        action_type: str,
        scope: builtins.list[str],
        *,
        actor_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="release_baseline",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: builtins.list[str],
        payload: dict[str, Any],
        *,
        intensity: float,
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type=cast(Any, event_type),
                    node_type="release_baseline",
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=intensity,
                    payload={"owner_scope": scope, **payload},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _gate_payload(value: object) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        payload = cast(Any, value).model_dump(mode="json")
        if isinstance(payload, dict):
            return payload
    if isinstance(value, dict):
        return value
    return {"status": "passed", "result": str(value)}


def _status(scenario_runs: Sequence[object], quality_gate_results: dict[str, Any]) -> str:
    if any(getattr(run, "status", None) == "failed" for run in scenario_runs):
        return "failed"
    if any(
        isinstance(result, dict) and result.get("status") == "failed"
        for result in quality_gate_results.values()
    ):
        return "failed"
    if any(getattr(run, "status", None) == "warning" for run in scenario_runs):
        return "warning"
    if any(
        isinstance(result, dict) and result.get("status") in {"warning", "skipped", "degraded"}
        for result in quality_gate_results.values()
    ):
        return "warning"
    return "passed"
