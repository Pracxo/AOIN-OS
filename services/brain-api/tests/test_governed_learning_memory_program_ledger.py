from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
)
from test_governed_learning_memory_program_authorization import (
    AUTH_ID,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    load_json,
)


def test_program_ledger_records_aion223_authorization_without_runtime_effects() -> None:
    program = load_json("docs/governed-learning-memory/program-ledger.json")
    assert program["program_id"] == PROGRAM_ID
    if program["program_state"] in {
        ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
        ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    }:
        assert program["active_glm_implementation_authorization"] == "AION-225-GLM-0003"
        assert program["active_glm_implementation_task"] == "AION-226"
    elif program["program_state"] == CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE:
        assert program["active_glm_implementation_authorization"] == "AION-227-GLM-0004"
        assert program["active_glm_implementation_task"] == "AION-228"
    else:
        assert program["active_glm_implementation_authorization"] == AUTH_ID
        assert program["active_glm_implementation_task"] == IMPLEMENTATION_TASK
    assert program["local_append_only_knowledge_store_authorized"] is True
    assert program["local_append_only_knowledge_store_implemented"] is True
    assert program["operator_invoked_local_persistence_available"] is True
    assert program["synthetic_local_persistence_pilot_completed"] is True
    assert program["runtime_enabled"] is False
    assert program["general_persistent_knowledge_write_enabled"] is False
    assert program["background_persistent_knowledge_write_enabled"] is False
    assert program["production_persistent_knowledge_write_enabled"] is False
    assert program["automatic_knowledge_promotion_enabled"] is False
    kinds = {item["record_kind"] for item in program["records"]}
    assert "operator_evaluation_closeout" in kinds
    assert "pending_implementation_authorization" in kinds
