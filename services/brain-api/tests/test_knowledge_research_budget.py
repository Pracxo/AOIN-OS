from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.knowledge_intelligence.research_budget import (
    ResearchResourceBudget,
    ResearchResourceUsage,
    evaluate_research_budget,
)


def test_default_budget_limits_are_exact():
    budget = ResearchResourceBudget()
    assert budget.maximum_queries_per_plan == 20
    assert budget.maximum_domains_per_plan == 20
    assert budget.maximum_source_candidates_per_plan == 100
    assert budget.maximum_fetches_per_plan == 50
    assert budget.maximum_redirects_per_fetch == 3
    assert budget.maximum_concurrency == 4
    assert budget.maximum_timeout_seconds_per_request == 20
    assert budget.maximum_wall_clock_seconds_per_plan == 900
    assert budget.maximum_response_bytes_per_source == 5242880
    assert budget.maximum_total_transfer_bytes_per_plan == 52428800
    assert budget.maximum_snapshot_records_per_plan == 100
    assert budget.maximum_safe_headers_per_snapshot == 32
    assert budget.maximum_citation_references_per_snapshot == 20
    assert budget.maximum_operator_review_items_per_plan == 50


def test_every_forbidden_counter_fails_closed():
    usage = ResearchResourceUsage(network_calls=1, knowledge_promotions=1)
    decision = evaluate_research_budget(usage, ResearchResourceBudget())
    assert not decision.within_budget
    assert decision.fail_closed
    assert decision.partial_unvalidated_outputs_discarded
    assert "network_calls_permitted" in decision.violations
    assert "knowledge_promotions" in decision.violations


def test_negative_usage_rejected_and_quality_cannot_override_violation():
    with pytest.raises(ValidationError):
        ResearchResourceUsage(query_count=-1)
    decision = evaluate_research_budget(
        ResearchResourceUsage(query_count=21),
        ResearchResourceBudget(),
    )
    assert decision.reason_codes == (
        "research_budget_exceeded",
        "research_plan_stopped_fail_closed",
    )
