from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import parse_content_type_header


def test_unsupported_content_type_rejects() -> None:
    assert parse_content_type_header("text/plain; charset=utf-8") == ("text/plain", "utf-8")
    with pytest.raises(ValueError):
        parse_content_type_header("application/octet-stream")
