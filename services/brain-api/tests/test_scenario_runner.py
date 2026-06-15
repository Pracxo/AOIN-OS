"""Scenario runner tests."""

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scenarios import ScenarioCreateRequest, ScenarioRunRequest, ScenarioStep
from aion_brain.scenarios.comparator import ScenarioComparator
from aion_brain.scenarios.repository import ScenarioRepository
from aion_brain.scenarios.runner import ScenarioRunner


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyCreatePolicy(AllowPolicy):
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        decision = super().authorize(request)
        if request.action_type == "scenario.create":
            return decision.model_copy(update={"allow": False, "reason": "denied"})
        return decision


class AllowAutonomy:
    def decide(self, request):  # type: ignore[no-untyped-def]
        return SimpleNamespace(allow=True, reason="allowed")


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def test_scenario_runner_creates_scenario_through_policy() -> None:
    runner = runner_with_policy(AllowPolicy())
    scenario = runner.create_scenario(
        ScenarioCreateRequest(
            scenario_id="scenario-1",
            name="Scenario",
            description="Generic scenario.",
            scenario_type="smoke",
            owner_scope=["workspace:main"],
            steps=[step("noop")],
        )
    )

    assert scenario.scenario_id == "scenario-1"


def test_policy_deny_blocks_scenario_create() -> None:
    runner = runner_with_policy(DenyCreatePolicy())

    with pytest.raises(AIONPolicyDeniedException):
        runner.create_scenario(
            ScenarioCreateRequest(
                name="Scenario",
                description="Generic scenario.",
                scenario_type="smoke",
                owner_scope=["workspace:main"],
                steps=[step("noop")],
            )
        )


def test_scenario_runner_dry_run_golden_path_passes_with_fakes() -> None:
    runner = runner_with_policy(AllowPolicy())
    result = runner.run(
        ScenarioRunRequest(
            scenario_id="golden_path_brain",
            owner_scope=["workspace:main"],
            mode="dry_run",
        )
    )

    assert result.status == "passed"
    assert result.passed_steps == 13
    assert result.result["external_calls"] is False


def test_required_step_failure_fails_run() -> None:
    runner = runner_with_policy(AllowPolicy())
    scenario = runner.create_scenario(
        ScenarioCreateRequest(
            name="Failure",
            description="Generic failure scenario.",
            scenario_type="smoke",
            owner_scope=["workspace:main"],
            steps=[step("noop", request={"force_fail": True}), step("noop")],
        )
    )

    result = runner.run(
        ScenarioRunRequest(
            scenario_id=scenario.scenario_id,
            owner_scope=["workspace:main"],
            fail_fast=False,
        )
    )

    assert result.status == "failed"
    assert result.failed_steps == 1
    assert result.skipped_steps == 1


def test_optional_step_failure_creates_warning() -> None:
    runner = runner_with_policy(AllowPolicy())
    scenario = runner.create_scenario(
        ScenarioCreateRequest(
            name="Warning",
            description="Generic warning scenario.",
            scenario_type="smoke",
            owner_scope=["workspace:main"],
            steps=[step("noop", required=False, request={"force_fail": True})],
        )
    )

    result = runner.run(
        ScenarioRunRequest(scenario_id=scenario.scenario_id, owner_scope=["workspace:main"])
    )

    assert result.status == "warning"
    assert result.failed_steps == 0


def test_scenario_runner_does_not_call_external_services() -> None:
    runner = runner_with_policy(AllowPolicy())

    result = runner.run(
        ScenarioRunRequest(scenario_id="golden_path_brain", owner_scope=["workspace:main"])
    )

    assert result.result["external_calls"] is False
    assert all(step.output.get("external_calls") is not True for step in result.steps)


def test_visual_telemetry_emits_scenario_events() -> None:
    telemetry = FakeTelemetry()
    runner = runner_with_policy(AllowPolicy(), telemetry=telemetry)

    runner.run(ScenarioRunRequest(scenario_id="golden_path_brain", owner_scope=["workspace:main"]))

    event_types = {getattr(event, "event_type", "") for event in telemetry.events}
    assert "scenario_started" in event_types
    assert "scenario_step_completed" in event_types
    assert "scenario_completed" in event_types


def runner_with_policy(policy: object, telemetry: object | None = None) -> ScenarioRunner:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ScenarioRunner(
        ScenarioRepository(engine=engine),
        ScenarioComparator(),
        policy,  # type: ignore[arg-type]
        autonomy_governor=AllowAutonomy(),
        telemetry_service=telemetry,
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
    )


def step(
    step_type: str,
    *,
    request: dict[str, object] | None = None,
    required: bool = True,
) -> ScenarioStep:
    return ScenarioStep(
        step_id=f"step-{step_type}",
        step_type=step_type,  # type: ignore[arg-type]
        description="Generic step.",
        request=request or {},
        expected={"required_keys": ["status"]},
        required=required,
    )
