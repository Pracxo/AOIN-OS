from __future__ import annotations

from test_governed_learning_memory_contracts import PROHIBITED_RUNTIME_TOKENS, source_text


def test_source_has_no_network_or_external_runtime_clients():
    text = source_text()

    for token in PROHIBITED_RUNTIME_TOKENS:
        assert token not in text
