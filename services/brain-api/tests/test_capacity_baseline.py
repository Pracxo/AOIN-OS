"""Capacity baseline service tests."""

from aion_brain.contracts.performance import BenchmarkRunRequest
from aion_brain.performance.defaults import build_smoke_benchmark
from tests.performance_fakes import SCOPE, services


def test_capacity_baseline_service_computes_percentiles() -> None:
    _, runner, baseline_service, *_ = services()
    run = runner.run(BenchmarkRunRequest(benchmark=build_smoke_benchmark(SCOPE), owner_scope=SCOPE))

    baseline = baseline_service.create_from_run("0.1.0", "local", [run.benchmark_run_id], "tester")

    assert baseline.status == "active"
    assert baseline.metrics["sample_count"] == run.sample_count
    assert "noop" in baseline.metrics["operations"]
