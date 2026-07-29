from __future__ import annotations

import pytest
from pydantic import ValidationError
from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

from aion_brain.contracts.governed_engagement_learning import (
    RESOURCE_LIMITS,
    EngagementApplicationResourceBudget,
    build_record,
    validate_parameter_codes,
    validate_reason_codes,
)


def test_aion226_resource_limits_match_authorization():
    assert dict(RESOURCE_LIMITS) == eval225.AION226_RESOURCE_LIMITS


def test_engagement_reason_and_parameter_registries_are_closed():
    with pytest.raises(ValueError):
        validate_reason_codes(("engagement_runtime_disabled", "unknown_reason"))

    with pytest.raises(ValueError):
        validate_parameter_codes(("review_required", "unbounded_parameter"))


def test_engagement_contract_fingerprints_are_strict():
    budget = build_record(
        EngagementApplicationResourceBudget,
        {
            "budget_id": "budget-contract-test",
            "limits": dict(RESOURCE_LIMITS),
            "runtime_effect": False,
        },
        "budget_fingerprint",
    )
    payload = budget.model_dump(mode="python")
    payload["budget_fingerprint"] = "f" * 64

    with pytest.raises(ValidationError):
        EngagementApplicationResourceBudget.model_validate(payload)
