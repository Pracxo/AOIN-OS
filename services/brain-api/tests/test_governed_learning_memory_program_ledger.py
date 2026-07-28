from __future__ import annotations

from test_governed_learning_memory_program_authorization import (
    AUTH_ID,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    PROGRAM_STATE,
    load_json,
)


def test_program_ledger_records_new_program_without_runtime_effects() -> None:
    program = load_json("docs/governed-learning-memory/program-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    assert program["program_state"] == PROGRAM_STATE
    assert program["created_by_task"] == "AION-221"
    assert program["active_glm_implementation_authorization"] == AUTH_ID
    assert program["active_glm_implementation_task"] == IMPLEMENTATION_TASK
    assert program["runtime_enabled"] is False
    assert program["persistent_knowledge_write_enabled"] is False
    assert program["cognitive_memory_write_enabled"] is False
    assert program["cognitive_belief_mutation_enabled"] is False
    assert program["automatic_knowledge_promotion_enabled"] is False

    records = program["records"]
    assert any(item["record_kind"] == "prerequisite_verification" for item in records)
    charter = next(item for item in records if item["record_kind"] == "program_charter")
    assert charter["task_id"] == "AION-221"
    assert charter["authorized_task"] == "AION-222"
    assert charter["runtime_effect"] is False
    assert charter["persistent_write_effect"] is False
    assert charter["source_mutation_effect"] is False
    assert charter["git_mutation_effect"] is False
