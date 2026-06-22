"""Golden path scenario catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aion_brain.contracts.golden_path import GoldenPathScenario
from aion_brain.golden_path.policy import authorize_golden_path_action
from aion_brain.golden_path.repository import GoldenPathRepository
from aion_brain.golden_path.telemetry import emit_golden_path_telemetry


class ScenarioCatalogService:
    """Manage default and persisted golden path scenarios."""

    def __init__(
        self,
        repository: GoldenPathRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def seed_default_scenarios(
        self,
        scope: list[str],
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Seed deterministic default scenarios."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.scenario.create",
            scope,
            actor_id=created_by,
            risk_level="medium",
            context={"dry_run": dry_run, "default_scenarios": True},
        )
        scenarios = default_scenarios(scope)
        if dry_run:
            return {
                "dry_run": True,
                "created": [],
                "scenarios": [scenario.model_dump(mode="json") for scenario in scenarios],
            }
        created = [self.create_scenario(scenario) for scenario in scenarios]
        return {
            "dry_run": False,
            "created": [scenario.golden_path_scenario_id for scenario in created],
            "scenarios": [scenario.model_dump(mode="json") for scenario in created],
        }

    def create_scenario(self, scenario: GoldenPathScenario) -> GoldenPathScenario:
        """Create or replace a golden path scenario."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.scenario.create",
            scenario.owner_scope,
            actor_id=scenario.created_by,
            resource_type="golden_path_scenario",
            resource_id=scenario.scenario_key,
            risk_level="medium",
            context={"external_calls": False, "scenario_owned": True},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_scenario(
            scenario.model_copy(
                update={
                    "created_at": scenario.created_at or now,
                    "updated_at": now,
                }
            )
        )
        emit_golden_path_telemetry(
            self._telemetry_service,
            event_type="golden_path_scenario_created",
            node_type="golden_path_scenario",
            node_id=saved.golden_path_scenario_id,
            scope=saved.owner_scope,
            intensity=0.4,
            payload={"scenario_key": saved.scenario_key, "scenario_type": saved.scenario_type},
        )
        return saved

    def list_scenarios(
        self,
        scope: list[str],
        status: str | None = None,
        scenario_type: str | None = None,
        limit: int = 100,
    ) -> list[GoldenPathScenario]:
        """List persisted scenarios plus built-in defaults."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.scenario.read",
            scope,
            resource_type="golden_path_scenario",
        )
        persisted = self._repository.list_scenarios(
            status=status,
            scenario_type=scenario_type,
            limit=limit,
        )
        existing = {scenario.scenario_key for scenario in persisted}
        defaults = [
            scenario
            for scenario in default_scenarios(scope)
            if scenario.scenario_key not in existing
        ]
        scenarios = [*persisted, *defaults]
        if status:
            scenarios = [scenario for scenario in scenarios if scenario.status == status]
        if scenario_type:
            scenarios = [
                scenario for scenario in scenarios if scenario.scenario_type == scenario_type
            ]
        return scenarios[:limit]

    def get_scenario(self, scenario_key: str, scope: list[str]) -> GoldenPathScenario | None:
        """Return one scenario by key."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.scenario.read",
            scope,
            resource_type="golden_path_scenario",
            resource_id=scenario_key,
        )
        return self._repository.get_scenario(scenario_key) or _default_by_key(scenario_key, scope)


def default_scenarios(scope: list[str]) -> list[GoldenPathScenario]:
    """Return all default golden path scenarios."""
    specs = [
        (
            "golden.boot.readiness",
            "Boot Readiness",
            "boot",
            ["diagnostics", "health", "runtime_config"],
        ),
        ("golden.self.describe", "Self Description", "generic", ["self_description"]),
        ("golden.dialogue.turn", "Dialogue Turn", "dialogue", ["dialogue", "responses"]),
        (
            "golden.instruction.resolve",
            "Instruction Resolution",
            "dialogue",
            ["instructions", "policy", "autonomy"],
        ),
        ("golden.prompt.compile", "Prompt Packet Compile", "prompt", ["prompts", "context"]),
        (
            "golden.model_output.govern",
            "Model Output Governance",
            "model_output",
            ["model_outputs"],
        ),
        (
            "golden.grounding.verify",
            "Grounding Verification",
            "grounding",
            ["grounding", "evidence"],
        ),
        (
            "golden.action.proposal.dry_run",
            "Action Proposal Dry Run",
            "action",
            ["action_proposals"],
        ),
        (
            "golden.execution.handoff.dry_run",
            "Execution Handoff Dry Run",
            "action",
            ["execution_handoff"],
        ),
        (
            "golden.run_supervision.sample",
            "Run Supervision Sample",
            "run_supervision",
            ["run_supervision"],
        ),
        ("golden.notification.alert", "Notification Alert", "notification", ["notifications"]),
        ("golden.scheduler.tick", "Scheduler Tick", "scheduler", ["scheduler"]),
        ("golden.incident.correlate", "Incident Correlation", "incident", ["incidents"]),
        ("golden.registry.validate", "Registry Validation", "registry", ["resource_registry"]),
        ("golden.lifecycle.evaluate", "Lifecycle Evaluation", "lifecycle", ["lifecycle"]),
        (
            "golden.contract.snapshot_scan",
            "Contract Snapshot Scan",
            "contract",
            ["contract_registry"],
        ),
        ("golden.extension.intake", "Extension Intake", "extension", ["extensions"]),
        (
            "golden.module_binding.validate",
            "Module Binding Validation",
            "binding",
            ["module_bindings"],
        ),
        ("golden.conformance.readiness", "Conformance Readiness", "conformance", ["conformance"]),
        ("golden.operator.overview", "Operator Overview", "operator", ["operator"]),
    ]
    return [
        _scenario(key, name, scenario_type, services, scope, index)
        for index, (key, name, scenario_type, services) in enumerate(specs, start=1)
    ]


def _scenario(
    key: str,
    name: str,
    scenario_type: str,
    services: list[str],
    scope: list[str],
    index: int,
) -> GoldenPathScenario:
    step_key = key.removeprefix("golden.")
    return GoldenPathScenario(
        golden_path_scenario_id=f"golden-path-scenario-{index:02d}",
        scenario_key=key,
        name=name,
        description=f"Deterministic dry-run verification for {name.lower()}.",
        status="active",
        scenario_type=scenario_type,  # type: ignore[arg-type]
        owner_scope=scope,
        required_services=services,
        steps=[
            {
                "step_key": step_key,
                "service_name": services[0],
                "action_name": step_key.replace(".", "_"),
                "dry_run": True,
                "scenario_owned": True,
            }
        ],
        assertions=[
            {
                "assertion_key": f"{step_key}.passed",
                "assertion_type": "status_equals",
                "path": f"steps.{step_key}.status",
                "expected": "passed",
                "severity": "high",
            },
            {
                "assertion_key": f"{step_key}.no_external_call",
                "assertion_type": "no_external_call",
                "severity": "critical",
            },
            {
                "assertion_key": f"{step_key}.no_execution",
                "assertion_type": "no_execution",
                "severity": "critical",
            },
        ],
        tags=["golden_path", scenario_type],
        metadata={"default": True, "dry_run_safe": True, "scenario_owned": True},
    )


def _default_by_key(scenario_key: str, scope: list[str]) -> GoldenPathScenario | None:
    for scenario in default_scenarios(scope):
        if scenario.scenario_key == scenario_key:
            return scenario
    return None


__all__ = ["ScenarioCatalogService", "default_scenarios"]
