from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_persistent_knowledge_writes_remain_disabled() -> None:
    program = load_json("docs/governed-learning-memory/program-ledger.json")
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    runtime = load_json("examples/governed-learning-memory/runtime-hold.json")

    for payload in (program, auth["prohibited_capabilities"], runtime):
        assert payload["persistent_knowledge_write_enabled"] is False
    assert auth["prohibited_capabilities"]["persistent_verified_knowledge_write_enabled"] is False
    assert auth["resource_limits"]["maximum_persistent_knowledge_writes"] == 0
    assert auth["resource_limits"]["maximum_persistent_verified_knowledge_writes"] == 0
