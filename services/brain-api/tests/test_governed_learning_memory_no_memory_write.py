from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_cognitive_memory_writes_remain_disabled() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    projection = load_json(
        "examples/governed-learning-memory/cognitive-memory-projection-plan.json"
    )

    for key in (
        "cognitive_memory_write_enabled",
        "semantic_memory_write_enabled",
        "episodic_memory_write_enabled",
        "procedural_memory_write_enabled",
    ):
        assert auth["prohibited_capabilities"][key] is False
        assert projection[key] is False
    assert auth["resource_limits"]["maximum_cognitive_memory_writes"] == 0
    assert auth["resource_limits"]["maximum_semantic_memory_writes"] == 0
    assert auth["resource_limits"]["maximum_episodic_memory_writes"] == 0
    assert auth["resource_limits"]["maximum_procedural_memory_writes"] == 0
