from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import (
    PublicResearchPolicyError,
    validate_method,
)


def test_only_get_and_head_are_allowed() -> None:
    assert validate_method("GET") == "GET"
    assert validate_method("HEAD") == "HEAD"
    with pytest.raises(PublicResearchPolicyError):
        validate_method("POST")
