"""Deterministic Golden Path runner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.golden_path import (
    GoldenPathAssertionResult,
    GoldenPathFixturePack,
    GoldenPathRun,
    GoldenPathRunRequest,
    GoldenPathScenario,
    GoldenPathStepResult,
)
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.contracts.operator import OperatorActionItem
from aion_brain.golden_path.assertions import AssertionEngine
from aion_brain.golden_path.fixtures import FixturePackService, default_fixture_packs
from aion_brain.golden_path.policy import authorize_golden_path_action
from aion_brain.golden_path.redaction import redact_golden_path_payload, safe_summary
from aion_brain.golden_path.reporting import GoldenPathReportService
from aion_brain.golden_path.repository import GoldenPathRepository
from aion_brain.golden_path.scenarios import ScenarioCatalogService
from aion_brain.golden_path.telemetry import emit_golden_path_telemetry


class GoldenPathRunner:
    """Run local deterministic golden path scenarios without external side effects."""

    def __init__(
        self,
        repository: GoldenPathRepository,
        scenario_catalog: ScenarioCatalogService,
        fixture_service: FixturePackService,
        assertion_engine: AssertionEngine,
        report_service: GoldenPathReportService,
        policy_adapter: object,
        *,
        autonomy_governor: object | None = None,
        notification_router: object | None = None,
        operator_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: Settings | None = None,
        service_dependencies: dict[str, object] | None = None,
    ) -> None:
        self._repository = repository
        self._scenario_catalog = scenario_catalog
        self._fixture_service = fixture_service
        self._assertion_engine = assertion_engine
        self._report_service = report_service
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._notification_router = notification_router
        self._operator_repository = operator_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings or get_settings()
        self._service_dependencies = service_dependencies or {}

    def run(self, request: GoldenPathRunRequest) -> GoldenPathRun:
        """Run selected or default golden path scenarios."""

        if not self._settings.golden_path_enabled:
            return self._blocked_run(request, "golden_path_disabled")
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.run",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="golden_path_run",
            resource_id=request.golden_path_run_id,
            risk_level="medium",
            context=_run_context(request),
        )
        autonomy_reason = self._autonomy_block_reason(request)
        if autonomy_reason is not None:
            return self._blocked_run(request, autonomy_reason)

        run_id = request.golden_path_run_id or f"golden-path-run-{uuid4().hex}"
        trace_id = request.trace_id or f"trace-golden-path-{uuid4().hex}"
        started_at = datetime.now(UTC)
        self._emit(
            "golden_path_run_started",
            "golden_path_run",
            run_id,
            request.owner_scope,
            0.6,
            {"mode": request.mode},
        )

        scenarios = self._resolve_scenarios(request)
        fixture_packs = self._resolve_fixture_packs(request)
        for scenario in scenarios:
            self._repository.save_scenario(scenario)
        for pack in fixture_packs:
            self._repository.save_fixture_pack(pack)

        step_results: list[GoldenPathStepResult] = []
        assertion_results: list[GoldenPathAssertionResult] = []
        failures: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        for scenario in scenarios:
            scenario_steps, scenario_context = self._run_scenario(
                request,
                run_id,
                trace_id,
                scenario,
                len(step_results),
            )
            step_results.extend(scenario_steps)
            scenario_assertions = self._assertion_engine.evaluate_many(
                scenario.assertions,
                scenario_context,
            )
            assertion_results.extend(scenario_assertions)
            failures.extend(_assertion_failures(scenario_assertions))
            warnings.extend(_step_warnings(scenario_steps))

        passed_count = len([item for item in step_results if item.status == "passed"])
        failed_count = len([item for item in step_results if item.status == "failed"])
        warning_count = len([item for item in step_results if item.status == "warning"])
        skipped_count = len([item for item in step_results if item.status == "skipped"])
        blocked_count = len([item for item in step_results if item.status == "blocked"])
        assertion_failed = len([item for item in assertion_results if item.status == "failed"])
        status = _run_status(
            request.mode,
            failed_count=failed_count + assertion_failed,
            warning_count=warning_count,
            blocked_count=blocked_count,
        )
        run = GoldenPathRun(
            golden_path_run_id=run_id,
            trace_id=trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id or self._settings.golden_path_workspace_id_default,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            scenarios=scenarios,
            fixture_packs=fixture_packs,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            passed_count=passed_count,
            failed_count=failed_count + assertion_failed,
            warning_count=warning_count,
            skipped_count=skipped_count,
            blocked_count=blocked_count,
            step_results=step_results,
            assertion_results=assertion_results,
            report_id=None,
            warnings=warnings,
            failures=failures,
            result={
                "deterministic": True,
                "dry_run": request.mode == "dry_run",
                "controlled": request.mode == "controlled",
                "external_calls": False,
                "tool_execution": False,
                "source_records_mutated": False,
                "scenario_count": len(scenarios),
                "fixture_pack_count": len(fixture_packs),
            },
            metadata={"include_release_smoke": request.include_release_smoke, **request.metadata},
            created_by=request.created_by,
            created_at=started_at,
        )
        saved = self._repository.save_run(run)
        report = self._report_service.create_report(saved)
        saved = self._repository.save_run(
            saved.model_copy(update={"report_id": report.golden_path_report_id})
        )
        self._record_audit(saved)
        self._record_provenance(saved)
        self._maybe_notify(request, saved)
        self._maybe_operator_item(request, saved)
        self._emit(
            "golden_path_run_completed"
            if saved.status not in {"failed", "blocked"}
            else "golden_path_run_failed",
            "golden_path_run",
            saved.golden_path_run_id,
            saved.owner_scope,
            1.0 if saved.status in {"failed", "blocked"} else 0.8,
            {"status": saved.status, "report_id": saved.report_id},
        )
        return saved

    def get_run(self, golden_path_run_id: str, scope: list[str]) -> GoldenPathRun | None:
        """Return one run."""

        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.run.read",
            scope,
            resource_type="golden_path_run",
            resource_id=golden_path_run_id,
        )
        return self._repository.get_run(golden_path_run_id)

    def list_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> list[GoldenPathRun]:
        """List runs."""

        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.run.read",
            scope,
            resource_type="golden_path_run",
        )
        return self._repository.list_runs(status=status, trace_id=trace_id, limit=limit)

    def latest_status(self, scope: list[str]) -> dict[str, Any]:
        """Return operator-friendly latest status."""

        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.report.read",
            scope,
            resource_type="golden_path_report",
        )
        return self._repository.status(scope)

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        """Return lightweight status for operator cards."""

        return self._repository.status(scope or [])

    def _resolve_scenarios(self, request: GoldenPathRunRequest) -> list[GoldenPathScenario]:
        if request.scenario_keys:
            scenarios = [
                scenario
                for key in request.scenario_keys
                if (scenario := self._scenario_catalog.get_scenario(key, request.owner_scope))
                is not None
            ]
        elif request.run_all_defaults:
            scenarios = self._scenario_catalog.list_scenarios(
                request.owner_scope,
                status="active",
                limit=100,
            )
        else:
            scenarios = []
        return [scenario for scenario in scenarios if scenario.status == "active"]

    def _resolve_fixture_packs(self, request: GoldenPathRunRequest) -> list[GoldenPathFixturePack]:
        if request.fixture_pack_keys:
            return [
                pack
                for key in request.fixture_pack_keys
                if (pack := self._fixture_service.get_fixture_pack(key, request.owner_scope))
                is not None
            ]
        return default_fixture_packs(
            request.owner_scope,
            request.workspace_id or self._settings.golden_path_workspace_id_default,
        )

    def _run_scenario(
        self,
        request: GoldenPathRunRequest,
        run_id: str,
        trace_id: str,
        scenario: GoldenPathScenario,
        offset: int,
    ) -> tuple[list[GoldenPathStepResult], dict[str, Any]]:
        context: dict[str, Any] = {
            "golden_path_run_id": run_id,
            "golden_path_scenario_id": scenario.golden_path_scenario_id,
            "trace_id": trace_id,
            "external_calls": False,
            "executed": False,
            "tool_execution": False,
            "source_records_mutated": False,
            "policy_allowed": True,
            "steps": {},
        }
        steps: list[GoldenPathStepResult] = []
        for index, definition in enumerate(scenario.steps, start=1):
            step_key = str(
                definition.get("step_key") or scenario.scenario_key.removeprefix("golden.")
            )
            service_name = str(definition.get("service_name") or _first_service(scenario))
            action_name = str(definition.get("action_name") or step_key.replace(".", "_"))
            available = self._service_available(service_name)
            status = "passed" if available else "blocked"
            output = _step_output(scenario, service_name, status, available)
            step = GoldenPathStepResult(
                step_result_id=f"golden-path-step-{uuid4().hex}",
                golden_path_run_id=run_id,
                golden_path_scenario_id=scenario.golden_path_scenario_id,
                trace_id=trace_id,
                step_key=step_key,
                step_order=offset + index,
                status=cast(Any, status),
                service_name=service_name,
                action_name=action_name,
                input_summary={
                    "scenario_key": scenario.scenario_key,
                    "mode": request.mode,
                    "fixture_pack_keys": request.fixture_pack_keys,
                },
                output_summary=output,
                resource_refs=[f"aion://golden_path_scenario/{scenario.golden_path_scenario_id}"],
                duration_ms=0,
                error={} if available else {"reason": "required_service_unavailable"},
                metadata={"dry_run": request.mode == "dry_run", "scenario_owned": True},
                created_at=datetime.now(UTC),
            )
            steps.append(step)
            _set_path(context["steps"], step_key.split("."), output)
            self._emit(
                "golden_path_step_completed",
                "golden_path_step",
                step.step_result_id,
                scenario.owner_scope,
                0.7 if available else 1.0,
                {"scenario_key": scenario.scenario_key, "status": status},
            )
        return steps, context

    def _service_available(self, service_name: str) -> bool:
        service = self._service_dependencies.get(service_name)
        if isinstance(service, bool):
            return service
        return service is not None

    def _autonomy_block_reason(self, request: GoldenPathRunRequest) -> str | None:
        if request.mode == "controlled" and not self._settings.golden_path_controlled_mode_enabled:
            return "controlled_mode_disabled"
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = "dry_run" if request.mode == "dry_run" else "supervised_controlled"
        try:
            decision = decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id or request.created_by,
                    workspace_id=request.workspace_id,
                    requested_mode=cast(Any, requested_mode),
                    action_type="golden_path.run",
                    resource_type="golden_path_run",
                    resource_id=request.golden_path_run_id,
                    risk_level="medium",
                    approval_present=request.mode == "controlled",
                    context=_run_context(request),
                )
            )
        except Exception as exc:
            return exc.__class__.__name__
        return (
            None
            if getattr(decision, "allow", False)
            else str(getattr(decision, "reason", "autonomy_denied"))
        )

    def _blocked_run(self, request: GoldenPathRunRequest, reason: str) -> GoldenPathRun:
        run_id = request.golden_path_run_id or f"golden-path-run-{uuid4().hex}"
        now = datetime.now(UTC)
        run = GoldenPathRun(
            golden_path_run_id=run_id,
            trace_id=request.trace_id or f"trace-golden-path-{uuid4().hex}",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id or self._settings.golden_path_workspace_id_default,
            status="blocked",
            mode=request.mode,
            owner_scope=request.owner_scope,
            scenarios=[],
            fixture_packs=[],
            started_at=now,
            completed_at=now,
            passed_count=0,
            failed_count=0,
            warning_count=0,
            skipped_count=0,
            blocked_count=1,
            step_results=[],
            assertion_results=[],
            report_id=None,
            warnings=[],
            failures=[{"reason": reason, "severity": "critical"}],
            result={
                "deterministic": True,
                "external_calls": False,
                "tool_execution": False,
                "source_records_mutated": False,
                "blocked_reason": reason,
            },
            metadata={"blocked_by": reason},
            created_by=request.created_by,
            created_at=now,
        )
        saved = self._repository.save_run(run)
        report = self._report_service.create_report(saved)
        saved = self._repository.save_run(
            saved.model_copy(update={"report_id": report.golden_path_report_id})
        )
        self._emit(
            "golden_path_run_blocked",
            "golden_path_run",
            saved.golden_path_run_id,
            saved.owner_scope,
            1.0,
            {"reason": reason},
        )
        return saved

    def _record_audit(self, run: GoldenPathRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="golden_path.run",
            resource_type="golden_path_run",
            resource_id=run.golden_path_run_id,
            event_type="golden_path_run_completed",
            outcome="completed" if run.status not in {"failed", "blocked"} else "blocked",
            source_component="golden_path_runner",
            trace_id=run.trace_id,
            actor_id=run.actor_id,
            workspace_id=run.workspace_id,
            risk_level="medium",
            payload={"status": run.status, "scenario_count": len(run.scenarios)},
        )

    def _record_provenance(self, run: GoldenPathRun) -> None:
        record = getattr(self._provenance_service, "record", None) or getattr(
            self._provenance_service,
            "link",
            None,
        )
        if callable(record):
            try:
                record(
                    source_type="golden_path_run",
                    source_id=run.golden_path_run_id,
                    target_refs=[scenario.golden_path_scenario_id for scenario in run.scenarios],
                )
            except Exception:
                return

    def _maybe_notify(self, request: GoldenPathRunRequest, run: GoldenPathRun) -> None:
        if not (
            request.create_notifications or self._settings.golden_path_create_notifications_default
        ):
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    topic_key="generic.info",
                    severity="high" if run.status in {"failed", "blocked"} else "info",
                    title="Golden path run completed",
                    message=f"Golden path run {run.golden_path_run_id} completed.",
                    source_type="generic",
                    source_id=run.golden_path_run_id,
                    target_type="operator",
                    target_id="operator",
                    owner_scope=run.owner_scope,
                    refs=[run.golden_path_run_id],
                    metadata={"status": run.status, "dry_run": run.mode == "dry_run"},
                    created_by=request.created_by,
                )
            )
        except Exception:
            return

    def _maybe_operator_item(self, request: GoldenPathRunRequest, run: GoldenPathRun) -> None:
        if not (
            request.create_operator_items
            or self._settings.golden_path_create_operator_items_default
        ):
            return
        if run.status not in {"failed", "blocked"} and not _critical_failures(run):
            return
        save = getattr(self._operator_repository, "save_action_item", None)
        if not callable(save):
            return
        try:
            save(
                OperatorActionItem(
                    action_item_id=f"operator-action-golden-path-{uuid4().hex}",
                    trace_id=run.trace_id,
                    source_type="golden_path_run",
                    source_id=run.golden_path_run_id,
                    category="release",
                    severity="critical" if _critical_failures(run) else "high",
                    status="open",
                    title="Golden path run needs operator review.",
                    description="A local deterministic golden path run has blockers or failures.",
                    recommended_action="review_golden_path_report",
                    runbook_ref="docs/operations/golden-path.md",
                    owner_scope=run.owner_scope,
                    metadata={"status": run.status, "report_id": run.report_id},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_golden_path_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            intensity=intensity,
            payload=payload,
        )


def _run_context(request: GoldenPathRunRequest) -> dict[str, Any]:
    return {
        "mode": request.mode,
        "dry_run": request.mode == "dry_run",
        "external_calls": False,
        "tool_execution": False,
        "source_records_mutated": False,
        "scenario_keys": request.scenario_keys,
        "fixture_pack_keys": request.fixture_pack_keys,
    }


def _run_status(
    mode: str,
    *,
    failed_count: int,
    warning_count: int,
    blocked_count: int,
) -> str:
    if blocked_count:
        return "blocked"
    if failed_count:
        return "failed"
    if warning_count:
        return "warning"
    return "dry_run" if mode == "dry_run" else "passed"


def _first_service(scenario: GoldenPathScenario) -> str:
    return scenario.required_services[0] if scenario.required_services else "generic"


def _step_output(
    scenario: GoldenPathScenario,
    service_name: str,
    status: str,
    available: bool,
) -> dict[str, Any]:
    return {
        "status": status,
        "scenario_key": scenario.scenario_key,
        "service_name": service_name,
        "service_available": available,
        "external_calls": False,
        "tool_execution": False,
        "source_records_mutated": False,
        "summary": safe_summary(
            f"{scenario.name} {'completed' if available else 'blocked'} in local dry-run harness."
        ),
    }


def _set_path(target: dict[str, Any], parts: list[str], value: dict[str, Any]) -> None:
    current = target
    for part in parts[:-1]:
        nested = current.setdefault(part, {})
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = redact_golden_path_payload(value)


def _assertion_failures(assertions: list[GoldenPathAssertionResult]) -> list[dict[str, Any]]:
    return [
        {
            "assertion_result_id": item.assertion_result_id,
            "assertion_key": item.assertion_key,
            "severity": item.severity,
            "message": item.message,
        }
        for item in assertions
        if item.status == "failed"
    ]


def _step_warnings(steps: list[GoldenPathStepResult]) -> list[dict[str, Any]]:
    return [
        {
            "step_result_id": item.step_result_id,
            "step_key": item.step_key,
            "status": item.status,
            "service_name": item.service_name,
        }
        for item in steps
        if item.status in {"warning", "skipped", "blocked"}
    ]


def _critical_failures(run: GoldenPathRun) -> list[GoldenPathAssertionResult]:
    return [
        item
        for item in run.assertion_results
        if item.status == "failed" and item.severity == "critical"
    ]


__all__ = ["GoldenPathRunner"]
