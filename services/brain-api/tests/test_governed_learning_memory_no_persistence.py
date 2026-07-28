from __future__ import annotations

from test_governed_learning_memory_contracts import source_text


def test_source_does_not_persist_knowledge_or_verified_memory():
    text = source_text()

    assert ".write_text(" not in text
    assert ".write_bytes(" not in text
    assert "persistent_knowledge_writes: Literal[0]" in text
    assert "persistent_verified_knowledge_writes: Literal[0]" in text
