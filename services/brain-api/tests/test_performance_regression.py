"""Performance regression tests."""

from aion_brain.contracts.performance import BenchmarkRunRequest
from aion_brain.performance.defaults import build_smoke_benchmark
from tests.performance_fakes import SCOPE, services


def test_performance_regression_comparator_detects_p95_regression() -> None:
    _, runner, baseline_service, _, comparator, *_ = services()
    baseline_run = runner.run(
        BenchmarkRunRequest(benchmark=build_smoke_benchmark(SCOPE), owner_scope=SCOPE)
    )
    baseline = baseline_service.create_from_run(
        "0.1.0",
        "local",
        [baseline_run.benchmark_run_id],
        "tester",
    )
    slow_benchmark = build_smoke_benchmark(SCOPE).model_copy(
        update={
            "benchmark_id": "benchmark-slow",
            "steps": [
                step.model_copy(update={"payload": {"duration_ms": 100}})
                for step in build_smoke_benchmark(SCOPE).steps
            ],
        }
    )
    slow_run = runner.run(BenchmarkRunRequest(benchmark=slow_benchmark, owner_scope=SCOPE))

    report = comparator.compare(slow_run, baseline)

    assert report.status == "failed"
    assert report.regressions


def test_performance_regression_comparator_detects_improvement() -> None:
    _, runner, baseline_service, _, comparator, *_ = services()
    slow_benchmark = build_smoke_benchmark(SCOPE).model_copy(
        update={
            "benchmark_id": "benchmark-slow-base",
            "steps": [
                step.model_copy(update={"payload": {"duration_ms": 100}})
                for step in build_smoke_benchmark(SCOPE).steps
            ],
        }
    )
    baseline_run = runner.run(BenchmarkRunRequest(benchmark=slow_benchmark, owner_scope=SCOPE))
    baseline = baseline_service.create_from_run(
        "0.1.0",
        "local",
        [baseline_run.benchmark_run_id],
        "tester",
    )
    fast_run = runner.run(
        BenchmarkRunRequest(benchmark=build_smoke_benchmark(SCOPE), owner_scope=SCOPE)
    )

    report = comparator.compare(fast_run, baseline)

    assert report.status == "passed"
    assert report.improvements
