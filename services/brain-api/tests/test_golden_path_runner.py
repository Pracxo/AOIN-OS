"""Golden Path runner tests."""

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.config import Settings
from aion_brain.contracts.autonomy import AutonomyDecision
from aion_brain.contracts.golden_path import GoldenPathRunRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.golden_path.assertions import AssertionEngine
from aion_brain.golden_path.fixtures import FixturePackService
from aion_brain.golden_path.reporting import GoldenPathReportService
from aion_brain.golden_path.repository import GoldenPathRepository
from aion_brain.golden_path.runner import GoldenPathRunner
from aion_brain.golden_path.scenarios import ScenarioCatalogService, default_scenarios


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


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied_for_test",
            constraints=[],
            audit_level="standard",
        )


class AllowAutonomy:
    def decide(self, _request: object) -> AutonomyDecision:
        return AutonomyDecision(
            autonomy_decision_id="autonomy-1",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            requested_mode="dry_run",
            resolved_mode="dry_run",
            action_type="golden_path.run",
            resource_type="golden_path_run",
            resource_id=None,
            risk_level="medium",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            created_at=None,
        )


def test_golden_path_runner_runs_default_scenarios_without_execution() -> None:
    runner, repository = _runner()

    run = runner.run(GoldenPathRunRequest(owner_scope=["workspace:main"]))

    assert run.status == "dry_run"
    assert run.failed_count == 0
    assert run.blocked_count == 0
    assert run.result["external_calls"] is False
    assert run.result["tool_execution"] is False
    assert run.report_id is not None
    report = repository.get_report(run.report_id)
    assert report is not None
    assert report.release_candidate_ready is True


def test_golden_path_runner_blocks_when_required_service_missing() -> None:
    runner, _repository = _runner(service_dependencies={"diagnostics": None})

    run = runner.run(
        GoldenPathRunRequest(
            owner_scope=["workspace:main"],
            scenario_keys=["golden.boot.readiness"],
            run_all_defaults=False,
        )
    )

    assert run.status == "blocked"
    assert run.blocked_count == 1
    assert run.report_id is not None


def test_golden_path_runner_policy_denial_fails_closed() -> None:
    runner, _repository = _runner(policy_adapter=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        runner.run(GoldenPathRunRequest(owner_scope=["workspace:main"]))


def _runner(
    *,
    policy_adapter: object | None = None,
    service_dependencies: dict[str, object] | None = None,
) -> tuple[GoldenPathRunner, GoldenPathRepository]:
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    policy = policy_adapter or AllowPolicy()
    repository = GoldenPathRepository(settings.database_url)
    scenario_catalog = ScenarioCatalogService(repository, policy)
    fixture_service = FixturePackService(repository, policy, settings=settings)
    assertion_engine = AssertionEngine()
    report_service = GoldenPathReportService(repository, policy, settings=settings)
    if service_dependencies is None:
        services = {
            service: object()
            for scenario in default_scenarios(["workspace:main"])
            for service in scenario.required_services
        }
    else:
        services = service_dependencies
    return (
        GoldenPathRunner(
            repository,
            scenario_catalog,
            fixture_service,
            assertion_engine,
            report_service,
            policy,
            autonomy_governor=AllowAutonomy(),
            settings=settings,
            service_dependencies=services,
        ),
        repository,
    )
