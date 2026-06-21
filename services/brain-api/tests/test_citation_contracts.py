from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.citations import CitationRecord, UnsupportedStatement


def test_citation_record_validates_type_and_secret_quote() -> None:
    payload = {
        "citation_id": "citation-1",
        "source_type": "evidence",
        "source_id": "evidence-1",
        "citation_type": "supports_statement",
        "label": "Evidence",
        "confidence": 0.7,
        "verified": True,
    }
    assert CitationRecord(**payload).citation_type == "supports_statement"

    with pytest.raises(ValidationError):
        CitationRecord(**{**payload, "citation_type": "not-valid"})

    with pytest.raises(ValidationError):
        CitationRecord(**{**payload, "quote": "sk-testsecretvalue"})


def test_unsupported_statement_rejects_hidden_reasoning() -> None:
    with pytest.raises(ValidationError):
        UnsupportedStatement(
            unsupported_statement_id="unsupported-1",
            statement_text="hidden_reasoning: private",
            statement_hash="hash",
            reason="unsupported",
            severity="high",
        )
