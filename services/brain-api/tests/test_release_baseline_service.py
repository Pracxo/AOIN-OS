"""Release baseline service tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.release_baseline import ReleaseBaselineRequest
from aion_brain.release_baseline.repository import ReleaseBaselineRepository
from aion_brain.release_baseline.service import ReleaseBaselineService
from aion_brain.scenarios.comparator import ScenarioComparator
from aion_brain.scenarios.repository import ScenarioRepository
from aion_brain.scenarios.runner import ScenarioRunner
from tests.test_scenario_runner import AllowAutonomy, AllowPolicy


class FailedGate:
    def generate(self) -> dict[str, str]:
        return {"status": "failed"}


def test_release_baseline_service_runs_selected_scenarios() -> None:
    service = baseline_service()

    report = service.run(
        ReleaseBaselineRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            scenario_ids=["golden_path_brain"],
            include_quality_gates=False,
        )
    )

    assert report.status == "passed"
    assert len(report.scenario_run_ids) == 1


def test_release_baseline_service_includes_quality_gate_results() -> None:
    service = baseline_service()

    report = service.run(
        ReleaseBaselineRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            scenario_ids=["golden_path_brain"],
        )
    )

    assert "kernel_self_test" in report.quality_gate_results


def test_release_baseline_service_fails_when_critical_gate_fails() -> None:
    service = baseline_service(policy_coverage=FailedGate())

    report = service.run(
        ReleaseBaselineRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            scenario_ids=["golden_path_brain"],
        )
    )

    assert report.status == "failed"
    assert "review_policy_coverage" in report.report["recommendations"]


def baseline_service(policy_coverage: object | None = None) -> ReleaseBaselineService:
    scenario_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    baseline_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    runner = ScenarioRunner(
        ScenarioRepository(engine=scenario_engine),
        ScenarioComparator(),
        AllowPolicy(),
        autonomy_governor=AllowAutonomy(),
        settings=settings,
    )
    return ReleaseBaselineService(
        runner,
        ReleaseBaselineRepository(engine=baseline_engine),
        AllowPolicy(),
        kernel_self_test={"status": "passed"},
        policy_coverage=policy_coverage or {"status": "passed"},
        openapi_hygiene={"status": "passed"},
        boundary_checker={"status": "passed"},
        contract_export={"status": "passed"},
        settings=settings,
    )
