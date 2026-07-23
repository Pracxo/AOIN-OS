from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.research_policy import (
    decode_research_text,
    validate_character_encoding,
)


@pytest.mark.parametrize(
    "encoding",
    ["utf-8", "utf-8-sig", "us-ascii", "iso-8859-1", "windows-1252"],
)
def test_approved_character_encodings_are_accepted(encoding: str):
    assert validate_character_encoding("text/plain", encoding) == encoding


def test_unsupported_or_malformed_encoding_is_rejected_without_body_echo():
    with pytest.raises(ValueError):
        validate_character_encoding("text/plain", "utf-16")
    with pytest.raises(UnicodeDecodeError) as exc_info:
        decode_research_text(b"\xff\xfe", "utf-8")
    assert "\\xff" not in str(exc_info.value)
