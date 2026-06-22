from __future__ import annotations

from aion_brain.prompts.hash import hash_prompt_text, normalize_prompt_text


def test_prompt_hash_normalizes_line_endings_and_trailing_space() -> None:
    assert normalize_prompt_text("hello  \r\nworld\n") == "hello\nworld"
    assert hash_prompt_text("hello\nworld") == hash_prompt_text("hello  \r\nworld\n")
