"""Deterministic scenario runner for AION Brain release validation."""

from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import (
    AIONNotFoundException,
    AIONPolicyDeniedException,
    AIONUnsupportedOperationException,
)
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scenarios import (
    ScenarioCreateRequest,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunRequest,
    ScenarioStep,
    ScenarioStepRun,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.scenarios.comparator import ScenarioComparator
from aion_brain.scenarios.defaults import list_default_scenarios
from aion_brain.scenarios.repository import ScenarioRepository

StepHandler = Callable[[ScenarioStep, ScenarioRunRequest, ScenarioDefinition], dict[str, Any]]


class ScenarioRunner:
    """Run deterministic side-effect-safe scenario definitions."""

    def __init__(
        self,
        repository: ScenarioRepository,
        comparator: ScenarioComparator,
        policy_adapter: PolicyAdapter,
        *,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        step_handlers: dict[str, StepHandler] | None = None,
        **service_dependencies: object,
    ) -> None:
        self._repository = repository
        self._comparator = comparator
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._step_handlers = step_handlers or {}
        self._service_dependencies = service_dependencies

    def create_scenario(self, request: ScenarioCreateRequest) -> ScenarioDefinition:
        """Create and persist a scenario definition."""
        if not request.owner_scope:
            request = request.model_copy(
                update={"owner_scope": [self._settings.scenario_default_owner_scope]}
            )
        self._require_policy(
            "scenario.create",
            request.owner_scope,
            actor_id=request.created_by,
            context={"scenario_type": request.scenario_type},
        )
        now = datetime.now(UTC)
        scenario = ScenarioDefinition(
            scenario_id=request.scenario_id or f"scenario-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active" if request.activate else "disabled",
            scenario_type=request.scenario_type,
            owner_scope=request.owner_scope,
            steps=request.steps,
            expected=request.expected,
            tags=request.tags,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None if request.activate else now,
        )
        saved = self._repository.save_definition(scenario)
        self._emit("scenario_created", saved.scenario_id, saved.owner_scope, {"name": saved.name})
        return saved

    def list_scenarios(
        self,
        status: str | None = None,
        scenario_type: str | None = None,
        tags: list[str] | None = None,
    ) -> list[ScenarioDefinition]:
        """List persisted scenarios plus built-in defaults."""
        scope = [self._settings.scenario_default_owner_scope]
        self._require_policy("scenario.read", scope, context={"status": status})
        persisted = self._repository.list_definitions(
            status=status,
            scenario_type=scenario_type,
            tags=tags,
        )
        existing_ids = {scenario.scenario_id for scenario in persisted}
        defaults = [
            scenario
            for scenario in list_default_scenarios(scope)
            if scenario.scenario_id not in existing_ids
        ]
        scenarios = [*persisted, *defaults]
        if status:
            scenarios = [scenario for scenario in scenarios if scenario.status == status]
        if scenario_type:
            scenarios = [
                scenario for scenario in scenarios if scenario.scenario_type == scenario_type
            ]
        if tags:
            requested = set(tags)
            scenarios = [scenario for scenario in scenarios if requested & set(scenario.tags)]
        return scenarios

    def get_scenario(self, scenario_id: str, scope: list[str]) -> ScenarioDefinition | None:
        """Return a scenario by ID."""
        self._require_policy(
            "scenario.read",
            scope,
            resource_id=scenario_id,
            context={"scenario_id": scenario_id},
        )
        return self._load_scenario(scenario_id, scope)

    def disable_scenario(
        self,
        scenario_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ScenarioDefinition:
        """Disable a persisted or built-in scenario."""
        scenario = self._repository.get_definition(scenario_id) or self._load_scenario(
            scenario_id,
            [self._settings.scenario_default_owner_scope],
        )
        if scenario is None:
            raise AIONNotFoundException("scenario_not_found")
        self._require_policy(
            "scenario.disable",
            scenario.owner_scope,
            actor_id=actor_id,
            resource_id=scenario_id,
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_definition(
            scenario.model_copy(
                update={
                    "status": "disabled",
                    "updated_at": now,
                    "disabled_at": now,
                    "metadata": {**scenario.metadata, "disabled_reason": reason},
                }
            )
        )
        return saved

    def run(self, request: ScenarioRunRequest) -> ScenarioRun:
        """Run one scenario and persist deterministic results."""
        if not request.owner_scope:
            request = request.model_copy(
                update={"owner_scope": [self._settings.scenario_default_owner_scope]}
            )
        scenario = request.scenario or self._load_scenario(
            cast(str, request.scenario_id),
            request.owner_scope,
        )
        if scenario is None:
            raise AIONNotFoundException("scenario_not_found")
        if not self._settings.scenarios_enabled:
            return self._blocked_run(request, scenario, "scenarios_disabled")
        decision = self._policy(
            "scenario.run",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            trace_id=request.trace_id,
            resource_id=scenario.scenario_id,
            risk_level="medium",
            context={"mode": request.mode, "scenario_id": scenario.scenario_id},
        )
        if not decision.get("allow", False):
            return self._blocked_run(request, scenario, str(decision.get("reason")))
        autonomy = self._autonomy_allows(request, scenario)
        if not autonomy["allow"]:
            return self._blocked_run(request, scenario, str(autonomy["reason"]))
        if request.mode == "controlled" and not self._settings.scenario_controlled_mode_enabled:
            return self._blocked_run(request, scenario, "controlled_scenarios_disabled")
        if scenario.status != "active":
            return self._blocked_run(request, scenario, "scenario_disabled")

        scenario_run_id = request.scenario_run_id or f"scenario-run-{uuid4().hex}"
        started = datetime.now(UTC)
        self._emit(
            "scenario_started",
            scenario_run_id,
            request.owner_scope,
            {"scenario_id": scenario.scenario_id, "mode": request.mode},
            trace_id=request.trace_id or scenario_run_id,
            intensity=0.5,
        )
        step_runs: list[ScenarioStepRun] = []
        failed_required = False
        for step in scenario.steps:
            if failed_required:
                step_runs.append(self._skipped_step(scenario_run_id, step))
                continue
            step_run = self._run_step(scenario_run_id, step, request, scenario)
            step_runs.append(step_run)
            if step_run.status == "failed" and step.required:
                failed_required = True
                if request.fail_fast:
                    break
        run = self._finalize_run(request, scenario, scenario_run_id, step_runs, started)
        self._repository.save_run(run)
        self._emit(
            "scenario_completed" if run.status != "failed" else "scenario_failed",
            scenario_run_id,
            request.owner_scope,
            {"scenario_id": scenario.scenario_id, "status": run.status},
            trace_id=run.trace_id or scenario_run_id,
            intensity=0.9 if run.status == "passed" else 1.0,
        )
        return run

    def get_run(self, scenario_run_id: str, scope: list[str]) -> ScenarioRun | None:
        """Return one scenario run."""
        self._require_policy(
            "scenario.read",
            scope,
            resource_id=scenario_run_id,
            context={"scenario_run_id": scenario_run_id},
        )
        run = self._repository.get_run(scenario_run_id)
        if run is None or not (set(scope) & set(run.owner_scope)):
            return None
        return run

    def list_runs(
        self,
        scope: list[str],
        status: str | None = None,
        scenario_type: str | None = None,
        limit: int = 50,
    ) -> list[ScenarioRun]:
        """List recent scenario runs."""
        self._require_policy("scenario.read", scope, context={"status": status})
        runs = self._repository.list_runs(scope=scope, status=status, limit=limit)
        if scenario_type:
            scenario_ids = {
                scenario.scenario_id
                for scenario in self.list_scenarios(scenario_type=scenario_type)
            }
            runs = [run for run in runs if run.scenario_id in scenario_ids]
        return runs

    def seed_default_scenarios(
        self,
        scope: list[str],
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Seed the built-in default scenario pack."""
        self._require_policy(
            "scenario.seed_defaults",
            scope,
            context={"dry_run": dry_run},
            risk_level="medium",
        )
        scenarios = list_default_scenarios(scope)
        if not dry_run:
            for scenario in scenarios:
                self._repository.save_definition(scenario)
        return {
            "seeded": 0 if dry_run else len(scenarios),
            "dry_run": dry_run,
            "scenario_ids": [scenario.scenario_id for scenario in scenarios],
        }

    def _run_step(
        self,
        scenario_run_id: str,
        step: ScenarioStep,
        request: ScenarioRunRequest,
        scenario: ScenarioDefinition,
    ) -> ScenarioStepRun:
        created_at = datetime.now(UTC)
        self._emit(
            "scenario_step_started",
            f"{scenario_run_id}:{step.step_id}",
            request.owner_scope,
            {"step_id": step.step_id, "step_type": step.step_type},
            trace_id=request.trace_id or scenario_run_id,
            intensity=0.5,
        )
        started = perf_counter()
        try:
            output = self._execute_step(step, request, scenario)
            comparison = self._comparator.compare_step_output(output, step.expected)
            if output.get("status") == "skipped":
                status = "skipped"
            elif comparison["passed"]:
                status = "passed"
            elif step.required:
                status = "failed"
            else:
                status = "warning"
            error: dict[str, Any] = {} if status in {"passed", "skipped"} else comparison
        except Exception as exc:
            output = {}
            error = {"reason": str(exc.__class__.__name__), "message": str(exc)}
            status = "failed" if step.required else "warning"
        completed_at = datetime.now(UTC)
        step_run = ScenarioStepRun(
            scenario_step_run_id=f"scenario-step-run-{uuid4().hex}",
            scenario_run_id=scenario_run_id,
            step_id=step.step_id,
            step_type=step.step_type,
            status=cast(Any, status),
            input=step.request,
            output=output,
            expected=step.expected,
            error=error,
            duration_ms=max(0, int((perf_counter() - started) * 1000)),
            created_at=created_at,
            completed_at=completed_at,
        )
        self._emit(
            "scenario_step_completed",
            step_run.scenario_step_run_id,
            request.owner_scope,
            {
                "step_id": step.step_id,
                "step_type": step.step_type,
                "status": step_run.status,
            },
            trace_id=request.trace_id or scenario_run_id,
            intensity=0.8 if step_run.status == "passed" else 1.0,
        )
        return step_run

    def _execute_step(
        self,
        step: ScenarioStep,
        request: ScenarioRunRequest,
        scenario: ScenarioDefinition,
    ) -> dict[str, Any]:
        if step.request.get("force_fail") is True:
            raise RuntimeError("forced_step_failure")
        handler = self._step_handlers.get(step.step_type)
        if handler is not None:
            return handler(step, request, scenario)
        if step.step_type in {"sdk_smoke", "cli_smoke"}:
            return {
                "status": "skipped",
                "reason": "handled_by_sdk_or_cli_layer",
                "external_calls": False,
            }
        if step.step_type == "health_check":
            return {
                "status": "ok",
                "service": self._settings.service_name,
                "version": self._settings.version,
            }
        if step.step_type == "kernel_status":
            return {"status": "ok", "kernel": "assembled", "external_calls": False}
        if step.step_type == "kernel_self_test":
            return {"status": "passed", "dry_run": True, "external_calls": False}
        return {
            "status": "ok",
            "step_type": step.step_type,
            "mode": request.mode,
            "scenario_id": scenario.scenario_id,
            "dry_run": request.mode == "dry_run",
            "external_calls": False,
            "optional_adapters_required": False,
        }

    def _skipped_step(self, scenario_run_id: str, step: ScenarioStep) -> ScenarioStepRun:
        now = datetime.now(UTC)
        return ScenarioStepRun(
            scenario_step_run_id=f"scenario-step-run-{uuid4().hex}",
            scenario_run_id=scenario_run_id,
            step_id=step.step_id,
            step_type=step.step_type,
            status="skipped",
            input=step.request,
            output={"status": "skipped", "reason": "previous_required_step_failed"},
            expected=step.expected,
            error={},
            duration_ms=0,
            created_at=now,
            completed_at=now,
        )

    def _finalize_run(
        self,
        request: ScenarioRunRequest,
        scenario: ScenarioDefinition,
        scenario_run_id: str,
        step_runs: list[ScenarioStepRun],
        started: datetime,
    ) -> ScenarioRun:
        failed_steps = sum(1 for step in step_runs if step.status == "failed")
        warning_steps = sum(1 for step in step_runs if step.status == "warning")
        passed_steps = sum(1 for step in step_runs if step.status == "passed")
        skipped_steps = sum(1 for step in step_runs if step.status == "skipped")
        status = "failed" if failed_steps else "warning" if warning_steps else "passed"
        run = ScenarioRun(
            scenario_run_id=scenario_run_id,
            scenario_id=scenario.scenario_id,
            trace_id=request.trace_id or scenario_run_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            step_count=len(step_runs),
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            steps=step_runs,
            result={
                "scenario_id": scenario.scenario_id,
                "status": status,
                "mode": request.mode,
                "external_calls": False,
                "started_at": started.isoformat(),
            },
            comparison={},
            created_by=request.created_by,
            created_at=started,
            completed_at=datetime.now(UTC),
        )
        return run.model_copy(
            update={"comparison": self._comparator.compare_run(run, scenario.expected)}
        )

    def _blocked_run(
        self,
        request: ScenarioRunRequest,
        scenario: ScenarioDefinition,
        reason: str,
    ) -> ScenarioRun:
        now = datetime.now(UTC)
        scenario_run_id = request.scenario_run_id or f"scenario-run-{uuid4().hex}"
        run = ScenarioRun(
            scenario_run_id=scenario_run_id,
            scenario_id=scenario.scenario_id,
            trace_id=request.trace_id or scenario_run_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="failed",
            mode=request.mode,
            owner_scope=request.owner_scope,
            step_count=0,
            passed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            steps=[],
            result={"status": "blocked", "reason": reason, "external_calls": False},
            comparison={"passed": False, "failures": [reason]},
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        self._repository.save_run(run)
        self._emit(
            "scenario_failed",
            scenario_run_id,
            request.owner_scope,
            {"scenario_id": scenario.scenario_id, "reason": reason},
            trace_id=run.trace_id,
            intensity=1.0,
        )
        return run

    def _load_scenario(self, scenario_id: str, scope: list[str]) -> ScenarioDefinition | None:
        persisted = self._repository.get_definition(scenario_id)
        if persisted is not None and set(scope) & set(persisted.owner_scope):
            return persisted
        for scenario in list_default_scenarios(scope):
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def _require_policy(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        trace_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy(
            action_type,
            scope,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=resource_id,
            risk_level=risk_level,
            context=context,
        )
        if not decision["allow"]:
            raise AIONPolicyDeniedException(str(decision["reason"]))

    def _policy(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        trace_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="scenario",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        return {"allow": decision.allow, "reason": decision.reason}

    def _autonomy_allows(
        self,
        request: ScenarioRunRequest,
        scenario: ScenarioDefinition,
    ) -> dict[str, Any]:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return {"allow": True, "reason": "no_autonomy_governor"}
        try:
            decision = decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode="dry_run",
                    action_type="scenario.run",
                    resource_type="scenario",
                    resource_id=scenario.scenario_id,
                    risk_level="medium",
                    approval_present=False,
                    context={"scenario_type": scenario.scenario_type},
                    metadata={"source": "scenario_runner"},
                )
            )
            return {
                "allow": bool(getattr(decision, "allow", False)),
                "reason": str(getattr(decision, "reason", "autonomy_denied")),
            }
        except Exception as exc:
            if self._settings.scenario_controlled_mode_enabled:
                return {"allow": False, "reason": f"autonomy_error:{exc.__class__.__name__}"}
            return {"allow": True, "reason": "autonomy_unavailable_in_dry_run"}

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, Any],
        *,
        trace_id: str | None = None,
        intensity: float = 0.5,
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        node_type = "scenario_step" if "step" in event_type else "scenario"
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=trace_id or node_id,
                    event_type=cast(Any, event_type),
                    node_type=cast(Any, node_type),
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


def require_scenarios_enabled(settings: Settings) -> None:
    """Raise when scenario APIs are disabled."""
    if not settings.scenarios_enabled:
        raise AIONUnsupportedOperationException("scenarios_disabled")
