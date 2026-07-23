from __future__ import annotations

from datetime import datetime

import pytest
from knowledge_research_test_helpers import valid_query
from pydantic import ValidationError

from aion_brain.contracts.knowledge_research import ResearchQuery, research_query_fingerprint


def test_valid_query_accepted_and_fingerprint_deterministic():
    query = valid_query()
    payload = {
        key: (value.isoformat() if isinstance(value, datetime) else value)
        for key, value in query.model_dump(exclude={"query_fingerprint"}).items()
    }
    assert research_query_fingerprint(payload) == research_query_fingerprint(payload)


def test_query_rejects_url_raw_transcript_and_executable_command():
    for text in (
        "Check https://research.example.invalid/source",
        "raw user message should not be stored",
        "please run curl https://example.invalid",
    ):
        with pytest.raises(ValidationError):
            ResearchQuery.model_validate({**valid_query().model_dump(), "research_question": text})


def test_query_rejects_duplicate_source_classes_and_domain_hint_overrun():
    with pytest.raises(ValidationError):
        ResearchQuery.model_validate(
            {
                **valid_query().model_dump(),
                "requested_source_classes": ("official_standard", "official_standard"),
            }
        )
    with pytest.raises(ValidationError):
        ResearchQuery.model_validate(
            {
                **valid_query().model_dump(),
                "domain_hints": tuple(f"d{i}.invalid" for i in range(21)),
            }
        )
