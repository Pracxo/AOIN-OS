"""Kernel performance wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_container_exposes_performance_services() -> None:
    container = kernel_container()

    assert container.performance_repository is not None
    assert container.benchmark_runner is not None
    assert container.capacity_baseline_service is not None
    assert container.resource_budget_service is not None
    assert container.performance_regression_comparator is not None
    assert container.performance_summary_service is not None


def test_kernel_diagnostics_include_performance_checks() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "benchmark_runner_present" in names
    assert "capacity_baseline_service_present" in names
    assert "performance_enabled" in names
    assert "benchmark_enabled" in names
    assert "performance_sampling_enabled" in names
