"""Deterministic local benchmark runner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.performance import (
    BenchmarkDefinition,
    BenchmarkRun,
    BenchmarkRunRequest,
    BenchmarkStep,
    PerformanceSample,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.performance.baseline import compute_run_metrics
from aion_brain.performance.defaults import list_default_benchmarks
from aion_brain.performance.regression import PerformanceRegressionComparator
from aion_brain.performance.repository import PerformanceRepository
from aion_brain.performance.timing import (
    duration_ms,
    estimate_json_size_bytes,
    now_monotonic_ms,
)
from aion_brain.policy.base import PolicyAdapter


class BenchmarkRunner:
    """Run local side-effect-safe benchmarks."""

    def __init__(
        self,
        repository: PerformanceRepository,
        policy_adapter: PolicyAdapter,
        *,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
        regression_comparator: PerformanceRegressionComparator | None = None,
        settings: Settings | None = None,
        services: dict[str, object] | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service
        self._regression_comparator = regression_comparator
        self._settings = settings or get_settings()
        self._services = services or {}

    def create_benchmark(self, definition: BenchmarkDefinition) -> BenchmarkDefinition:
        """Persist a benchmark definition after policy approval."""
        self._authorize(
            "performance.benchmark.create",
            definition.owner_scope,
            actor_id=definition.created_by,
            resource_id=definition.benchmark_id,
            risk_level="medium",
            context={"benchmark_type": definition.benchmark_type},
        )
        saved = self._repository.save_benchmark(definition)
        self._emit(
            "benchmark_created",
            "benchmark",
            saved.benchmark_id,
            {"benchmark_type": saved.benchmark_type},
            0.4,
        )
        return saved

    def list_benchmarks(
        self,
        *,
        status: str | None = None,
        benchmark_type: str | None = None,
    ) -> list[BenchmarkDefinition]:
        """List benchmark definitions."""
        return self._repository.list_benchmarks(status=status, benchmark_type=benchmark_type)

    def get_benchmark(
        self,
        benchmark_id: str,
        scope: list[str],
    ) -> BenchmarkDefinition | None:
        """Return one benchmark definition."""
        self._authorize(
            "performance.benchmark.read",
            scope,
            resource_id=benchmark_id,
            context={"benchmark_id": benchmark_id},
        )
        return self._repository.get_benchmark(benchmark_id)

    def seed_defaults(self, scope: list[str], *, dry_run: bool = True) -> dict[str, Any]:
        """Create or preview default local benchmark definitions."""
        definitions = list_default_benchmarks(scope)
        if not dry_run:
            for definition in definitions:
                self.create_benchmark(definition)
        return {
            "seeded": not dry_run,
            "dry_run": dry_run,
            "benchmark_count": len(definitions),
            "benchmark_ids": [definition.benchmark_id for definition in definitions],
        }

    def run(self, request: BenchmarkRunRequest) -> BenchmarkRun:
        """Run a local benchmark and persist the result."""
        run_id = request.benchmark_run_id or f"benchmark-run-{uuid4().hex}"
        started = datetime.now(UTC)
        self._emit(
            "benchmark_started",
            "benchmark",
            run_id,
            {"mode": request.mode},
            0.5,
        )
        if not self._settings.benchmark_enabled:
            return self._blocked_run(request, run_id, "benchmark_disabled", started)
        self._authorize(
            "performance.benchmark.run",
            request.owner_scope,
            actor_id=request.actor_id,
            resource_id=request.benchmark_id,
            risk_level="low",
            context={"mode": request.mode, "dry_run": request.mode == "dry_run"},
        )
        autonomy_reason = _autonomy_block_reason(
            self._autonomy_governor,
            "performance.benchmark.run",
            request.owner_scope,
        )
        if autonomy_reason:
            return self._blocked_run(request, run_id, autonomy_reason, started)
        if request.mode == "controlled" and not self._settings.benchmark_controlled_mode_enabled:
            return self._blocked_run(request, run_id, "controlled_benchmark_disabled", started)

        benchmark = self._load_benchmark(request)
        samples: list[PerformanceSample] = []
        for step in benchmark.steps:
            for iteration in range(step.repeat * request.repeat):
                sample = self._run_step(step, request, run_id, iteration)
                samples.append(sample)
                self._emit(
                    "benchmark_step_completed",
                    "performance",
                    sample.performance_sample_id,
                    {
                        "operation_type": sample.operation_type,
                        "status": sample.status,
                        "duration_ms": sample.duration_ms,
                    },
                    0.4,
                )

        failed_required = [
            sample
            for sample in samples
            if sample.status == "failed"
            and any(
                step.operation_type == sample.operation_type and step.required
                for step in benchmark.steps
            )
        ]
        warning_count = sum(1 for sample in samples if sample.status == "warning")
        failed_count = sum(1 for sample in samples if sample.status == "failed")
        status = (
            "failed"
            if failed_required
            else ("warning" if warning_count or failed_count else "passed")
        )
        report: dict[str, Any] = {
            "benchmark_id": benchmark.benchmark_id,
            "benchmark_type": benchmark.benchmark_type,
            "external_calls": False,
            "operation_metrics": compute_run_metrics(
                [
                    BenchmarkRun(
                        benchmark_run_id=run_id,
                        benchmark_id=benchmark.benchmark_id,
                        status="passed",
                        mode=request.mode,
                        owner_scope=request.owner_scope,
                        samples=samples,
                        sample_count=len(samples),
                        passed_count=0,
                        failed_count=0,
                        warning_count=0,
                    )
                ]
            ).get("operations", {}),
        }
        run = BenchmarkRun(
            benchmark_run_id=run_id,
            benchmark_id=benchmark.benchmark_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            samples=samples,
            sample_count=len(samples),
            passed_count=sum(1 for sample in samples if sample.status == "passed"),
            failed_count=failed_count,
            warning_count=warning_count,
            summary={
                "duration_ms": sum(sample.duration_ms for sample in samples),
                "operation_count": len({sample.operation_type for sample in samples}),
            },
            report=report,
            created_by=request.created_by,
            created_at=started,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_run(run)
        if request.compare_to_baseline_id and self._regression_comparator is not None:
            baseline = self._repository.get_baseline(request.compare_to_baseline_id)
            if baseline is not None:
                regression = self._regression_comparator.compare(saved, baseline)
                saved.report["regression_report_id"] = regression.regression_report_id
                if request.fail_on_regression and regression.status == "failed":
                    saved = saved.model_copy(update={"status": "failed"})
                    self._repository.save_run(saved)
        self._emit(
            "benchmark_completed" if saved.status != "failed" else "benchmark_failed",
            "benchmark",
            saved.benchmark_run_id,
            {"status": saved.status, "sample_count": saved.sample_count},
            0.9 if saved.status == "passed" else 1.0,
        )
        return saved

    def get_run(self, benchmark_run_id: str, scope: list[str]) -> BenchmarkRun | None:
        """Return one benchmark run."""
        self._authorize("performance.benchmark.read", scope, resource_id=benchmark_run_id)
        return self._repository.get_run(benchmark_run_id)

    def list_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        benchmark_type: str | None = None,
        limit: int = 50,
    ) -> list[BenchmarkRun]:
        """List benchmark runs."""
        self._authorize("performance.benchmark.read", scope, context={"limit": limit})
        return self._repository.list_runs(
            status=status,
            benchmark_type=benchmark_type,
            limit=limit,
        )

    def _load_benchmark(self, request: BenchmarkRunRequest) -> BenchmarkDefinition:
        if request.benchmark is not None:
            return request.benchmark
        if request.benchmark_id is None:
            raise AIONNotFoundException("benchmark_not_found")
        benchmark = self._repository.get_benchmark(request.benchmark_id)
        if benchmark is None:
            raise AIONNotFoundException("benchmark_not_found")
        return benchmark

    def _run_step(
        self,
        step: BenchmarkStep,
        request: BenchmarkRunRequest,
        run_id: str,
        iteration: int,
    ) -> PerformanceSample:
        start_ms = now_monotonic_ms()
        error: dict[str, Any] = {}
        status = str(step.payload.get("force_status", "passed"))
        if status not in {"passed", "failed", "warning", "skipped"}:
            status = "failed"
            error = {"reason": "invalid_forced_status"}
        simulated_duration = step.payload.get("duration_ms")
        if isinstance(simulated_duration, int | float):
            measured = max(0, int(simulated_duration))
        else:
            _execute_local_operation(step.operation_type, self._services)
            measured = max(1, duration_ms(start_ms, now_monotonic_ms()))
        if step.threshold_ms is not None and measured > step.threshold_ms and status == "passed":
            status = "warning"
        if status != step.expected_status and step.required:
            if status == "warning" and step.expected_status == "passed":
                pass
            else:
                error = error or {"reason": "unexpected_status"}
                status = "failed"
        return PerformanceSample(
            performance_sample_id=f"performance-sample-{uuid4().hex}",
            trace_id=request.trace_id,
            benchmark_run_id=run_id,
            operation_type=step.operation_type,
            component=step.operation_type,
            status=cast(Any, status),
            duration_ms=measured,
            input_size_bytes=estimate_json_size_bytes(step.payload),
            output_size_bytes=estimate_json_size_bytes({"status": status}),
            item_count=1,
            error=error,
            metadata={
                "step_id": step.step_id,
                "iteration": iteration,
                "required": step.required,
                "external_calls": False,
            },
            created_at=datetime.now(UTC),
        )

    def _blocked_run(
        self,
        request: BenchmarkRunRequest,
        run_id: str,
        reason: str,
        started: datetime,
    ) -> BenchmarkRun:
        run = BenchmarkRun(
            benchmark_run_id=run_id,
            benchmark_id=request.benchmark_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="failed",
            mode=request.mode,
            owner_scope=request.owner_scope,
            samples=[],
            sample_count=0,
            passed_count=0,
            failed_count=1,
            warning_count=0,
            summary={"reason": reason},
            report={"external_calls": False, "blocked": True},
            created_by=request.created_by,
            created_at=started,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_run(run)
        self._emit("benchmark_failed", "benchmark", saved.benchmark_run_id, {"reason": reason}, 1.0)
        return saved

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
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
                resource_type="performance",
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
        node_type: str,
        node_id: str,
        payload: dict[str, Any],
        intensity: float,
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        from aion_brain.contracts.telemetry import VisualTelemetryEvent

        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type=event_type,  # type: ignore[arg-type]
                    node_type=node_type,  # type: ignore[arg-type]
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


def _execute_local_operation(operation_type: str, services: dict[str, object]) -> None:
    del services
    supported = {
        "health",
        "kernel_status",
        "kernel_self_test",
        "event_ingest",
        "memory_create",
        "memory_retrieve",
        "evidence_ingest",
        "evidence_search",
        "retrieval_query",
        "context_compile",
        "reasoning_deterministic",
        "planning",
        "brain_think",
        "command_noop",
        "event_dispatch_dry_run",
        "workflow_dry_run",
        "cycle_dry_run",
        "visual_map",
        "backup_dry_run",
        "release_baseline_dry_run",
        "api_request",
        "noop",
    }
    if operation_type not in supported:
        raise ValueError("unsupported_operation")


def _autonomy_block_reason(
    autonomy_governor: object | None,
    action_type: str,
    scope: list[str],
) -> str | None:
    evaluate = getattr(autonomy_governor, "evaluate", None)
    if not callable(evaluate):
        return None
    try:
        decision = evaluate(action_type=action_type, scope=scope)
    except TypeError:
        return None
    allowed = getattr(decision, "allow", True)
    if allowed:
        return None
    return str(getattr(decision, "reason", "blocked_by_autonomy"))
