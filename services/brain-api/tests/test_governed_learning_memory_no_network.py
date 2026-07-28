from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION222_SOURCE_SCOPE,
)
from test_governed_learning_memory_contracts import PROHIBITED_RUNTIME_TOKENS
from test_governed_learning_memory_program_authorization import REPO_ROOT


def test_source_has_no_network_or_external_runtime_clients():
    text = "\n".join(
        (REPO_ROOT / relative).read_text(encoding="utf-8")
        for relative in AION222_SOURCE_SCOPE
    )

    for token in PROHIBITED_RUNTIME_TOKENS:
        assert token not in text
