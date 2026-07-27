from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import parse_content_type_header


def test_invalid_charset_rejects() -> None:
    with pytest.raises(ValueError):
        parse_content_type_header("text/plain; charset=utf-16")
