from __future__ import annotations

from aion_brain.dialogue.hashing import hash_message_content, normalize_message_content


def test_dialogue_hashing_is_deterministic() -> None:
    first = hash_message_content("hello\r\nworld   ")
    second = hash_message_content("hello\nworld")

    assert first == second


def test_normalize_message_content_strips_trailing_whitespace() -> None:
    assert normalize_message_content("hello   \r\nworld   ") == "hello\nworld"
