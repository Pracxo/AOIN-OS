from __future__ import annotations

from aion_brain.beliefs.claim_extractor import ClaimExtractor
from aion_brain.contracts.beliefs import ClaimExtractionRequest


def test_claim_extractor_extracts_simple_declarative_sentence() -> None:
    result = ClaimExtractor().extract(
        ClaimExtractionRequest(
            source_type="user_message",
            source_id="message-1",
            text="The local workspace has a configured belief layer.",
            owner_scope=["workspace:main"],
        )
    )

    assert len(result.extracted_claims) == 1
    assert result.extracted_claims[0].claim_type == "user_statement"


def test_claim_extractor_skips_questions() -> None:
    result = ClaimExtractor().extract(
        ClaimExtractionRequest(
            source_type="user_message",
            source_id="message-1",
            text="What is the current status?",
            owner_scope=["workspace:main"],
        )
    )

    assert result.extracted_claims == []


def test_claim_extractor_skips_secret_like_content() -> None:
    result = ClaimExtractor().extract(
        ClaimExtractionRequest(
            source_type="user_message",
            source_id="message-1",
            text="The token is sk-test-value.",
            owner_scope=["workspace:main"],
        )
    )

    assert result.extracted_claims == []
