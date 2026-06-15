"""Kernel scenario harness wiring tests."""

from aion_brain.release_baseline.service import ReleaseBaselineService
from aion_brain.scenarios.fixtures import DemoFixtureService
from aion_brain.scenarios.runner import ScenarioRunner
from tests.kernel_fakes import kernel_container


def test_kernel_container_registers_scenario_services() -> None:
    container = kernel_container()

    assert isinstance(container.get("scenario_runner"), ScenarioRunner)
    assert isinstance(container.get("demo_fixture_service"), DemoFixtureService)
    assert isinstance(container.get("release_baseline_service"), ReleaseBaselineService)


def test_kernel_diagnostics_include_scenario_checks() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "scenarios_enabled" in names
    assert "release_baseline_enabled" in names
    assert "scenario_runner_present" in names
    assert "demo_fixture_service_present" in names
    assert "release_baseline_service_present" in names
