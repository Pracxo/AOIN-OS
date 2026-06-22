from __future__ import annotations

from aion_brain.grounding.hash import hash_source_content, normalize_source_text


def test_hash_source_content_is_deterministic() -> None:
    assert normalize_source_text("one\r\n two") == "one two"
    assert hash_source_content("one\n two") == hash_source_content("one two")
