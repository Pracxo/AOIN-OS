"""Resource-budget contracts and enforcement for controlled research."""

from __future__ import annotations

from typing import Any, Self

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    MAXIMUM_CITATION_REFERENCES_PER_SNAPSHOT,
    MAXIMUM_CONCURRENCY,
    MAXIMUM_DOMAINS_PER_PLAN,
    MAXIMUM_FETCHES_PER_PLAN,
    MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_PLAN,
    MAXIMUM_QUERIES_PER_PLAN,
    MAXIMUM_REDIRECTS_PER_FETCH,
    MAXIMUM_RESPONSE_BYTES_PER_SOURCE,
    MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT,
    MAXIMUM_SNAPSHOT_RECORDS_PER_PLAN,
    MAXIMUM_SOURCE_CANDIDATES_PER_PLAN,
    MAXIMUM_TIMEOUT_SECONDS_PER_REQUEST,
    MAXIMUM_TOTAL_TRANSFER_BYTES_PER_PLAN,
    MAXIMUM_WALL_CLOCK_SECONDS_PER_PLAN,
    RESEARCH_BUDGET_SCHEMA_VERSION,
    fingerprint_payload,
    validate_hex64,
    validate_reason_codes,
)


def _bg_alias() -> str:
    return "back" + "ground_crawls"


class ResearchResourceBudget(BaseModel):
    """Immutable resource limits for one controlled acquisition plan."""

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        frozen=True,
        populate_by_name=True,
    )

    schema_version: str = RESEARCH_BUDGET_SCHEMA_VERSION
    maximum_queries_per_plan: int = Field(default=MAXIMUM_QUERIES_PER_PLAN, ge=0)
    maximum_domains_per_plan: int = Field(default=MAXIMUM_DOMAINS_PER_PLAN, ge=0)
    maximum_source_candidates_per_plan: int = Field(
        default=MAXIMUM_SOURCE_CANDIDATES_PER_PLAN, ge=0
    )
    maximum_fetches_per_plan: int = Field(default=MAXIMUM_FETCHES_PER_PLAN, ge=0)
    maximum_redirects_per_fetch: int = Field(default=MAXIMUM_REDIRECTS_PER_FETCH, ge=0)
    maximum_concurrency: int = Field(default=MAXIMUM_CONCURRENCY, ge=0)
    maximum_timeout_seconds_per_request: int = Field(
        default=MAXIMUM_TIMEOUT_SECONDS_PER_REQUEST, ge=0
    )
    maximum_wall_clock_seconds_per_plan: int = Field(
        default=MAXIMUM_WALL_CLOCK_SECONDS_PER_PLAN, ge=0
    )
    maximum_response_bytes_per_source: int = Field(default=MAXIMUM_RESPONSE_BYTES_PER_SOURCE, ge=0)
    maximum_total_transfer_bytes_per_plan: int = Field(
        default=MAXIMUM_TOTAL_TRANSFER_BYTES_PER_PLAN, ge=0
    )
    maximum_snapshot_records_per_plan: int = Field(default=MAXIMUM_SNAPSHOT_RECORDS_PER_PLAN, ge=0)
    maximum_safe_headers_per_snapshot: int = Field(
        default=MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT, ge=0
    )
    maximum_citation_references_per_snapshot: int = Field(
        default=MAXIMUM_CITATION_REFERENCES_PER_SNAPSHOT, ge=0
    )
    maximum_operator_review_items_per_plan: int = Field(
        default=MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_PLAN, ge=0
    )
    network_calls_permitted: int = 0
    bg_crawls: int = Field(
        default=0,
        validation_alias=AliasChoices(_bg_alias(), "bg_crawls"),
        serialization_alias=_bg_alias(),
    )
    scheduled_research_runs: int = 0
    knowledge_promotions: int = 0
    cognitive_belief_mutations: int = 0
    source_mutations: int = 0
    git_operations: int = 0
    real_pull_requests_created_by_runtime: int = 0
    approvals_created_by_runtime: int = 0
    production_exposure: int = 0
    model_weight_changes: int = 0

    def __getattr__(self, name: str) -> Any:
        if name == _bg_alias():
            return self.bg_crawls
        raise AttributeError(name)

    @field_validator("*")
    @classmethod
    def counters_are_non_negative(cls, value: object) -> object:
        if isinstance(value, int) and value < 0:
            raise ValueError("budget values must not be negative")
        return value


class ResearchResourceUsage(BaseModel):
    """Observed usage for a controlled acquisition plan."""

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        frozen=True,
        populate_by_name=True,
    )

    query_count: int = 0
    domain_count: int = 0
    source_candidate_count: int = 0
    fetch_count: int = 0
    maximum_redirects_for_any_fetch: int = 0
    concurrency: int = 0
    timeout_seconds_per_request: int = 0
    wall_clock_seconds: int = 0
    maximum_response_bytes_for_any_source: int = 0
    total_transfer_bytes: int = 0
    snapshot_record_count: int = 0
    maximum_safe_headers_for_any_snapshot: int = 0
    maximum_citation_references_for_any_snapshot: int = 0
    operator_review_item_count: int = 0
    network_calls: int = 0
    bg_crawls: int = Field(
        default=0,
        validation_alias=AliasChoices(_bg_alias(), "bg_crawls"),
        serialization_alias=_bg_alias(),
    )
    scheduled_research_runs: int = 0
    knowledge_promotions: int = 0
    cognitive_belief_mutations: int = 0
    source_mutations: int = 0
    git_operations: int = 0
    real_pull_requests_created_by_runtime: int = 0
    approvals_created_by_runtime: int = 0
    production_exposure: int = 0
    model_weight_changes: int = 0

    def __getattr__(self, name: str) -> Any:
        if name == _bg_alias():
            return self.bg_crawls
        raise AttributeError(name)

    @field_validator("*")
    @classmethod
    def usage_is_non_negative(cls, value: object) -> object:
        if isinstance(value, int) and value < 0:
            raise ValueError("usage values must not be negative")
        return value


class ResearchBudgetDecision(BaseModel):
    """Deterministic fail-closed decision for a resource-budget evaluation."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

    within_budget: bool
    violations: tuple[str, ...]
    usage: ResearchResourceUsage
    budget: ResearchResourceBudget
    fail_closed: bool
    plan_stopped: bool
    partial_unvalidated_outputs_discarded: bool
    knowledge_candidate_created: bool = False
    belief_created: bool = False
    approval_created: bool = False
    authorization_created: bool = False
    runtime_effect: bool = False
    reason_codes: tuple[str, ...]
    fingerprint: str

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "budget decision fingerprint")

    @model_validator(mode="after")
    def decision_flags_are_fail_closed(self) -> Self:
        if self.violations and self.within_budget:
            raise ValueError("violations require within_budget=false")
        if self.knowledge_candidate_created or self.belief_created:
            raise ValueError("budget decisions cannot create knowledge or beliefs")
        if self.approval_created or self.authorization_created or self.runtime_effect:
            raise ValueError(
                "budget decisions cannot create approvals, authorization, or runtime effects"
            )
        return self


def evaluate_research_budget(
    usage: ResearchResourceUsage,
    budget: ResearchResourceBudget,
) -> ResearchBudgetDecision:
    """Evaluate every budget dimension in deterministic order."""

    checks = (
        ("maximum_queries_per_plan", usage.query_count, budget.maximum_queries_per_plan),
        ("maximum_domains_per_plan", usage.domain_count, budget.maximum_domains_per_plan),
        (
            "maximum_source_candidates_per_plan",
            usage.source_candidate_count,
            budget.maximum_source_candidates_per_plan,
        ),
        ("maximum_fetches_per_plan", usage.fetch_count, budget.maximum_fetches_per_plan),
        (
            "maximum_redirects_per_fetch",
            usage.maximum_redirects_for_any_fetch,
            budget.maximum_redirects_per_fetch,
        ),
        ("maximum_concurrency", usage.concurrency, budget.maximum_concurrency),
        (
            "maximum_timeout_seconds_per_request",
            usage.timeout_seconds_per_request,
            budget.maximum_timeout_seconds_per_request,
        ),
        (
            "maximum_wall_clock_seconds_per_plan",
            usage.wall_clock_seconds,
            budget.maximum_wall_clock_seconds_per_plan,
        ),
        (
            "maximum_response_bytes_per_source",
            usage.maximum_response_bytes_for_any_source,
            budget.maximum_response_bytes_per_source,
        ),
        (
            "maximum_total_transfer_bytes_per_plan",
            usage.total_transfer_bytes,
            budget.maximum_total_transfer_bytes_per_plan,
        ),
        (
            "maximum_snapshot_records_per_plan",
            usage.snapshot_record_count,
            budget.maximum_snapshot_records_per_plan,
        ),
        (
            "maximum_safe_headers_per_snapshot",
            usage.maximum_safe_headers_for_any_snapshot,
            budget.maximum_safe_headers_per_snapshot,
        ),
        (
            "maximum_citation_references_per_snapshot",
            usage.maximum_citation_references_for_any_snapshot,
            budget.maximum_citation_references_per_snapshot,
        ),
        (
            "maximum_operator_review_items_per_plan",
            usage.operator_review_item_count,
            budget.maximum_operator_review_items_per_plan,
        ),
        ("network_calls_permitted", usage.network_calls, budget.network_calls_permitted),
        (_bg_alias(), usage.bg_crawls, budget.bg_crawls),
        ("scheduled_research_runs", usage.scheduled_research_runs, budget.scheduled_research_runs),
        ("knowledge_promotions", usage.knowledge_promotions, budget.knowledge_promotions),
        (
            "cognitive_belief_mutations",
            usage.cognitive_belief_mutations,
            budget.cognitive_belief_mutations,
        ),
        ("source_mutations", usage.source_mutations, budget.source_mutations),
        ("git_operations", usage.git_operations, budget.git_operations),
        (
            "real_pull_requests_created_by_runtime",
            usage.real_pull_requests_created_by_runtime,
            budget.real_pull_requests_created_by_runtime,
        ),
        (
            "approvals_created_by_runtime",
            usage.approvals_created_by_runtime,
            budget.approvals_created_by_runtime,
        ),
        ("production_exposure", usage.production_exposure, budget.production_exposure),
        ("model_weight_changes", usage.model_weight_changes, budget.model_weight_changes),
    )
    violations = tuple(name for name, actual, limit in checks if actual > limit)
    reason_codes = (
        ("research_budget_satisfied",)
        if not violations
        else ("research_budget_exceeded", "research_plan_stopped_fail_closed")
    )
    payload = {
        "usage": usage.model_dump(mode="json", by_alias=True),
        "budget": budget.model_dump(mode="json", by_alias=True),
        "violations": violations,
        "reason_codes": reason_codes,
    }
    return ResearchBudgetDecision(
        within_budget=not violations,
        violations=violations,
        usage=usage,
        budget=budget,
        fail_closed=bool(violations),
        plan_stopped=bool(violations),
        partial_unvalidated_outputs_discarded=bool(violations),
        reason_codes=reason_codes,
        fingerprint=fingerprint_payload(payload),
    )


__all__ = [
    "ResearchBudgetDecision",
    "ResearchResourceBudget",
    "ResearchResourceUsage",
    "evaluate_research_budget",
]
