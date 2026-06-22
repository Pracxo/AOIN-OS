"""Resource budget tests."""

from aion_brain.contracts.performance import PerformanceSample, ResourceBudgetProfile
from tests.performance_fakes import SCOPE, services


def test_resource_budget_service_evaluates_over_threshold_sample() -> None:
    _, _, _, budget_service, *_ = services()
    profile = ResourceBudgetProfile(
        resource_budget_profile_id="budget-1",
        name="Local budget",
        description="Generic budget",
        owner_scope=SCOPE,
        budgets={"max_request_duration_ms": 10},
        enforcement_mode="report_only",
    )
    sample = PerformanceSample(
        performance_sample_id="sample-1",
        operation_type="api_request",
        component="/health",
        status="passed",
        duration_ms=20,
    )

    result = budget_service.evaluate_sample(sample, profile)

    assert result["status"] == "warning"
