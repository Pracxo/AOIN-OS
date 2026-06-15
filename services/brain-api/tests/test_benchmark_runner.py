"""Benchmark runner tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.performance import BenchmarkDefinition, BenchmarkRunRequest, BenchmarkStep
from aion_brain.performance.defaults import build_smoke_benchmark
from tests.performance_fakes import SCOPE, DenyPolicy, services


def test_benchmark_runner_creates_benchmark_through_policy() -> None:
    _, runner, *_ = services()

    saved = runner.create_benchmark(build_smoke_benchmark(SCOPE))

    assert saved.benchmark_type == "smoke"


def test_policy_deny_blocks_benchmark_create() -> None:
    _, runner, *_ = services(policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        runner.create_benchmark(build_smoke_benchmark(SCOPE))


def test_benchmark_runner_dry_run_smoke_benchmark_passes() -> None:
    _, runner, *_ = services()

    run = runner.run(BenchmarkRunRequest(benchmark=build_smoke_benchmark(SCOPE), owner_scope=SCOPE))

    assert run.status == "passed"
    assert run.sample_count == 3


def test_benchmark_runner_required_step_failure_fails_run() -> None:
    _, runner, *_ = services()
    benchmark = BenchmarkDefinition(
        benchmark_id="benchmark-fail",
        name="Failing benchmark",
        description="Generic failure benchmark",
        benchmark_type="smoke",
        owner_scope=SCOPE,
        steps=[
            BenchmarkStep(
                step_id="fail",
                operation_type="noop",
                description="fail",
                payload={"force_status": "failed"},
            )
        ],
    )

    run = runner.run(BenchmarkRunRequest(benchmark=benchmark, owner_scope=SCOPE))

    assert run.status == "failed"


def test_benchmark_runner_optional_step_failure_creates_warning() -> None:
    _, runner, *_ = services()
    benchmark = BenchmarkDefinition(
        benchmark_id="benchmark-warning",
        name="Warning benchmark",
        description="Generic warning benchmark",
        benchmark_type="smoke",
        owner_scope=SCOPE,
        steps=[
            BenchmarkStep(
                step_id="optional",
                operation_type="noop",
                description="optional",
                payload={"force_status": "failed"},
                required=False,
            )
        ],
    )

    run = runner.run(BenchmarkRunRequest(benchmark=benchmark, owner_scope=SCOPE))

    assert run.status == "warning"


def test_benchmark_runner_controlled_mode_blocked_when_disabled() -> None:
    _, runner, *_ = services()

    run = runner.run(
        BenchmarkRunRequest(
            benchmark=build_smoke_benchmark(SCOPE),
            owner_scope=SCOPE,
            mode="controlled",
        )
    )

    assert run.status == "failed"
    assert run.summary["reason"] == "controlled_benchmark_disabled"
