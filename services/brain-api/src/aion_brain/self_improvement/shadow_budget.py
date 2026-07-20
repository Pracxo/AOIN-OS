"""Resource budgets for the controlled self-improvement shadow plane."""

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow import (
    FROZEN_MODEL_CONFIG,
    SHADOW_BUDGET_SCHEMA_VERSION,
    fingerprint_model,
    require_finite_number,
    require_reason_codes,
)


class ShadowResourceBudget(BaseModel):
    """Maximum authorized resource budget for one shadow run."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_BUDGET_SCHEMA_VERSION
    maximum_observation_references: int = 1000
    maximum_evaluation_records: int = 1000
    maximum_failure_patterns: int = 100
    maximum_hypotheses: int = 50
    maximum_regression_test_proposals: int = 25
    maximum_shadow_proposals: int = 10
    maximum_concurrency: int = 4
    maximum_wall_clock_seconds: float = 1800.0
    maximum_benchmark_cost_units: int = 50
    maximum_output_bytes: int = 10485760
    maximum_operator_output_files: int = 20
    network_calls: int = 0
    git_operations: int = 0
    source_mutations: int = 0
    real_pull_requests: int = 0
    runtime_promotions: int = 0

    @field_validator("*")
    @classmethod
    def budget_values_are_non_negative(cls, value: int | float | str) -> int | float | str:
        if isinstance(value, int | float):
            require_finite_number(float(value))
            if value < 0:
                raise ValueError("shadow budget cannot be negative")
        return value

    @model_validator(mode="after")
    def exact_zero_side_effect_budgets(self) -> ShadowResourceBudget:
        if self.maximum_concurrency > 4:
            raise ValueError("shadow concurrency cannot exceed four")
        if any(
            (
                self.network_calls,
                self.git_operations,
                self.source_mutations,
                self.real_pull_requests,
                self.runtime_promotions,
            )
        ):
            raise ValueError("shadow side-effect budgets must be zero")
        return self


class ShadowResourceUsage(BaseModel):
    """Observed resource usage for one shadow run."""

    model_config = FROZEN_MODEL_CONFIG

    observation_references: int = 0
    evaluation_records: int = 0
    failure_patterns: int = 0
    hypotheses: int = 0
    regression_test_proposals: int = 0
    shadow_proposals: int = 0
    concurrency: int = 0
    wall_clock_seconds: float = 0.0
    benchmark_cost_units: int = 0
    output_bytes: int = 0
    output_files: int = 0
    network_calls: int = 0
    git_operations: int = 0
    source_mutations: int = 0
    real_pull_requests: int = 0
    runtime_promotions: int = 0

    @field_validator("*")
    @classmethod
    def usage_values_are_non_negative(cls, value: int | float) -> int | float:
        require_finite_number(float(value))
        if value < 0:
            raise ValueError("shadow resource usage cannot be negative")
        return value


class ShadowBudgetDecision(BaseModel):
    """Fail-closed budget decision for a shadow run."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    violations: tuple[str, ...]
    usage: ShadowResourceUsage
    budget: ShadowResourceBudget
    run_stopped: bool
    fail_closed: bool
    quality_override_allowed: bool = False
    reason_codes: tuple[str, ...]
    fingerprint: str = ""

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_reason_codes(value)

    @model_validator(mode="after")
    def decision_is_consistent(self) -> ShadowBudgetDecision:
        if self.quality_override_allowed:
            raise ValueError("shadow budget cannot allow quality override")
        expected_stopped = bool(self.violations)
        if self.within_budget == expected_stopped:
            raise ValueError("shadow budget decision is inconsistent")
        if self.run_stopped != expected_stopped or self.fail_closed != expected_stopped:
            raise ValueError("shadow budget must fail closed on violations")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


def evaluate_shadow_budget(
    usage: ShadowResourceUsage,
    budget: ShadowResourceBudget,
) -> ShadowBudgetDecision:
    """Evaluate every budget dimension in deterministic order."""

    checks = (
        (
            "maximum_observation_references",
            usage.observation_references,
            budget.maximum_observation_references,
        ),
        ("maximum_evaluation_records", usage.evaluation_records, budget.maximum_evaluation_records),
        ("maximum_failure_patterns", usage.failure_patterns, budget.maximum_failure_patterns),
        ("maximum_hypotheses", usage.hypotheses, budget.maximum_hypotheses),
        (
            "maximum_regression_test_proposals",
            usage.regression_test_proposals,
            budget.maximum_regression_test_proposals,
        ),
        ("maximum_shadow_proposals", usage.shadow_proposals, budget.maximum_shadow_proposals),
        ("maximum_concurrency", usage.concurrency, budget.maximum_concurrency),
        ("maximum_wall_clock_seconds", usage.wall_clock_seconds, budget.maximum_wall_clock_seconds),
        (
            "maximum_benchmark_cost_units",
            usage.benchmark_cost_units,
            budget.maximum_benchmark_cost_units,
        ),
        ("maximum_output_bytes", usage.output_bytes, budget.maximum_output_bytes),
        ("maximum_operator_output_files", usage.output_files, budget.maximum_operator_output_files),
        ("network_calls", usage.network_calls, budget.network_calls),
        ("git_operations", usage.git_operations, budget.git_operations),
        ("source_mutations", usage.source_mutations, budget.source_mutations),
        ("real_pull_requests", usage.real_pull_requests, budget.real_pull_requests),
        ("runtime_promotions", usage.runtime_promotions, budget.runtime_promotions),
    )
    violations = tuple(name for name, observed, maximum in checks if observed > maximum)
    reason_codes = (
        ("shadow_budget_satisfied",)
        if not violations
        else ("shadow_budget_exceeded", "shadow_run_stopped_fail_closed")
    )
    return ShadowBudgetDecision(
        within_budget=not violations,
        violations=violations,
        usage=usage,
        budget=budget,
        run_stopped=bool(violations),
        fail_closed=bool(violations),
        reason_codes=reason_codes,
    )


__all__ = [
    "ShadowBudgetDecision",
    "ShadowResourceBudget",
    "ShadowResourceUsage",
    "evaluate_shadow_budget",
]
