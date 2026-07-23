from __future__ import annotations

from datetime import timedelta

import pytest
from knowledge_research_test_helpers import NOW, valid_candidate, valid_plan, valid_query
from pydantic import ValidationError

from aion_brain.contracts.knowledge_research import ResearchPlan


def test_plan_limits_and_read_methods_are_enforced():
    assert valid_plan().allowed_methods == ("GET", "HEAD")
    with pytest.raises(ValidationError):
        ResearchPlan.model_validate({**valid_plan().model_dump(), "allowed_methods": ("POST",)})
    with pytest.raises(ValidationError):
        ResearchPlan.model_validate(
            {
                **valid_plan().model_dump(),
                "queries": tuple(valid_query(f"q-{i}") for i in range(21)),
            }
        )


def test_plan_rejects_duplicate_ids_and_urls():
    candidate = valid_candidate("candidate-002")
    with pytest.raises(ValidationError):
        ResearchPlan.model_validate(
            {**valid_plan().model_dump(), "explicit_source_candidates": (candidate, candidate)}
        )


def test_plan_rejects_expired_long_or_runtime_enabled_values():
    plan = valid_plan().model_dump()
    for update in (
        {"expires_at": NOW},
        {"expires_at": NOW + timedelta(days=2)},
        {"background_execution": True},
        {"research_runtime_enabled": True},
        {"knowledge_promotion_enabled": True},
        {"cognitive_belief_mutation_enabled": True},
    ):
        with pytest.raises(ValidationError):
            ResearchPlan.model_validate({**plan, **update})


def test_http_policy_adapter_requires_allowlist():
    with pytest.raises(ValidationError):
        ResearchPlan.model_validate(
            {
                **valid_plan(adapter_type="operator_invoked_http").model_dump(),
                "explicit_domain_allowlist": (),
            }
        )
