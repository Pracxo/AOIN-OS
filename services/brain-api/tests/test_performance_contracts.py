"""Performance contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.performance import (
    BenchmarkDefinition,
    BenchmarkRunRequest,
    BenchmarkStep,
    CapacityBaseline,
    PerformanceSample,
    ResourceBudgetProfile,
)
from tests.performance_fakes import SCOPE


def test_performance_sample_validates_duration() -> None:
    with pytest.raises(ValidationError):
        PerformanceSample(
            performance_sample_id="sample-1",
            operation_type="health",
            component="health",
            status="passed",
            duration_ms=-1,
        )


def test_benchmark_step_validates_operation_type() -> None:
    with pytest.raises(ValidationError):
        BenchmarkStep(
            step_id="step-1",
            operation_type="domain.specific",
            description="invalid",
        )


def test_benchmark_definition_rejects_empty_steps() -> None:
    with pytest.raises(ValidationError):
        BenchmarkDefinition(
            benchmark_id="benchmark-1",
            name="Benchmark",
            description="Generic benchmark",
            benchmark_type="smoke",
            owner_scope=SCOPE,
            steps=[],
        )


def test_benchmark_run_request_validates_repeat() -> None:
    with pytest.raises(ValidationError):
        BenchmarkRunRequest(
            benchmark_id="benchmark-1",
            owner_scope=SCOPE,
            repeat=21,
        )


def test_capacity_baseline_rejects_empty_version() -> None:
    with pytest.raises(ValidationError):
        CapacityBaseline(
            capacity_baseline_id="baseline-1",
            version="",
            baseline_name="local",
            status="active",
        )


def test_resource_budget_profile_validates_enforcement_mode() -> None:
    with pytest.raises(ValidationError):
        ResourceBudgetProfile(
            resource_budget_profile_id="budget-1",
            name="budget",
            description="Generic budget",
            owner_scope=SCOPE,
            budgets={"max_request_duration_ms": 100},
            enforcement_mode="enforce",
            created_at=datetime.now(UTC),
        )
