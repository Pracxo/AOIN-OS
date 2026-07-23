from __future__ import annotations

from datetime import datetime

import pytest
from knowledge_research_test_helpers import valid_plan, valid_query
from pydantic import ValidationError

from aion_brain.contracts.knowledge_research import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    RESEARCH_REASON_CODES,
    ResearchPlan,
    ResearchQuery,
    validate_reason_codes,
)


def test_contract_constants_match_authorization_scope():
    assert PROGRAM_ID == "AION-KNOWLEDGE-INTELLIGENCE-001"
    assert AUTHORIZATION_TRANSACTION_ID == "AION-204-KI-0001"
    assert IMPLEMENTATION_TASK == "AION-205"
    assert FORMAL_CLOSEOUT_TASK == "AION-206"
    assert AUTHORIZATION_SCOPE == (
        "disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core"
    )
    assert len(RESEARCH_REASON_CODES) == len(set(RESEARCH_REASON_CODES))


def test_extra_fields_and_malformed_fingerprints_are_rejected():
    with pytest.raises(ValidationError):
        ResearchQuery.model_validate({**valid_query().model_dump(), "extra": True})
    with pytest.raises(ValidationError):
        ResearchQuery.model_validate({**valid_query().model_dump(), "query_fingerprint": "bad"})


def test_naive_and_non_utc_timestamps_are_rejected():
    with pytest.raises(ValidationError):
        ResearchQuery.model_validate(
            {**valid_query().model_dump(), "created_at": datetime(2026, 1, 1)}
        )


def test_wrong_program_authorization_or_task_is_rejected():
    for key, value in (
        ("program_id", "WRONG"),
        ("authorization_transaction_id", "AION-000"),
        ("implementation_task", "AION-206"),
    ):
        with pytest.raises(ValidationError):
            ResearchPlan.model_validate({**valid_plan().model_dump(), key: value})


def test_immutable_evidence_and_protected_material_rejection_without_echo():
    query = valid_query()
    with pytest.raises(ValidationError) as exc_info:
        ResearchQuery.model_validate(
            {**query.model_dump(), "research_question": "contains sk-secretvalue"}
        )
    assert "sk-secretvalue" not in str(exc_info.value)
    with pytest.raises(ValidationError):
        query.query_id = "changed"  # type: ignore[misc]


def test_reason_code_registry_rejects_unknown_and_duplicates():
    assert validate_reason_codes(("research_plan_valid",)) == ("research_plan_valid",)
    with pytest.raises(ValidationError):
        ResearchPlan.model_validate({**valid_plan().model_dump(), "plan_fingerprint": "x"})
    with pytest.raises(ValueError):
        validate_reason_codes(("research_plan_valid", "research_plan_valid"))
    with pytest.raises(ValueError):
        validate_reason_codes(("attacker://host/path",))
