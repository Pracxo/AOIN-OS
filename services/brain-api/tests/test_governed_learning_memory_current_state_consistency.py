from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT

APPLICATION_STATE = "implemented_deterministic_operator_approved_non_factual_in_memory_shadow_only"
PROGRAM_STATE = (
    "governed_learning_memory_controlled_local_continual_learning_pilot_"
    "implemented_completed_pending_final_closeout"
)
FINAL_PENDING_STATE = (
    "governed_learning_memory_final_evaluation_complete_pending_git_reconciliation"
)
COMPLETE_STATE = "governed_learning_memory_program_complete"


def test_current_state_marks_continual_learning_pilot_implemented_pending_closeout():
    ledger = json.loads(
        (REPO_ROOT / "docs/governed-learning-memory/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    if ledger["program_state"] in {FINAL_PENDING_STATE, COMPLETE_STATE}:
        assert ledger["current_authorization"] is None
        assert ledger["active_glm_implementation_authorization_count"] == 0
    else:
        assert (
            ledger["current_authorization"]["authorization_transaction_id"]
            == "AION-227-GLM-0004"
        )
        assert ledger["current_authorization"]["authorized_task"] == "AION-228"
    assert ledger["knowledge_promotion_transaction_core"]["implemented"] is True
    assert ledger["knowledge_promotion_transaction_core"]["runtime_writes_enabled"] is False
    assert ledger["promotion_transaction_operator_evaluation_passed"] is True
    assert ledger["local_append_only_knowledge_store_authorized"] is True
    assert ledger["local_append_only_knowledge_store_implemented"] is True
    assert ledger["operator_invoked_local_persistence_available"] is True
    assert ledger["synthetic_local_persistence_pilot_completed"] is True
    assert ledger["production_persistent_knowledge_write_enabled"] is False
    assert ledger["actual_belief_creation_enabled"] is False
    assert ledger["runtime_enabled"] is False
    assert ledger["engagement_learning_application_authorized"] is True
    assert ledger["engagement_learning_application_implemented"] is True
    assert ledger["engagement_learning_application_state"] == APPLICATION_STATE
    assert ledger["operator_invoked_engagement_shadow_application_available"] is True
    assert ledger["engagement_application_operator_evaluation_passed"] is True
    assert ledger["controlled_local_continual_learning_pilot_authorized"] is True
    assert ledger["controlled_local_continual_learning_pilot_implemented"] is True
    assert ledger["operator_invoked_continual_learning_pilot_available"] is (
        ledger["program_state"] == PROGRAM_STATE
    )
    assert ledger["deterministic_continual_learning_simulation_available"] is True
    assert ledger["controlled_live_pilot_completed"] is True
    assert ledger["controlled_live_pilot_cycle_count"] == 3


def test_aion228_current_state_preserves_aion229_closeout_boundary():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    program = json.loads(
        (root / "docs/governed-learning-memory/program-ledger.json").read_text()
    )
    assert program["program_state"] in {PROGRAM_STATE, FINAL_PENDING_STATE, COMPLETE_STATE}
    if program["program_state"] == PROGRAM_STATE:
        assert program["active_glm_implementation_authorization"] == "AION-227-GLM-0004"
        assert program["active_glm_implementation_task"] == "AION-228"
        assert program["formal_closeout_task"] == "AION-229"
    else:
        assert program["active_glm_implementation_authorization"] is None
        assert program["active_glm_implementation_task"] is None
        expected_closeout = (
            "AION-229" if program["program_state"] == FINAL_PENDING_STATE else None
        )
        assert program["formal_closeout_task"] == expected_closeout
    assert program["engagement_learning_application_authorized"] is True
    assert program["engagement_learning_application_implemented"] is True
    assert program["operator_invoked_engagement_shadow_application_available"] is True
    assert program["operator_invoked_continual_learning_pilot_authorized"] is True
    assert program["operator_invoked_continual_learning_pilot_available"] is (
        program["program_state"] == PROGRAM_STATE
    )
    assert program["controlled_local_continual_learning_pilot_implemented"] is True
    assert program["controlled_live_pilot_completed"] is True
    assert program["controlled_live_pilot_cycle_count"] == 3
    assert program["persistent_engagement_overlay_write_enabled"] is False
    assert program["aion_224_store_write_enabled"] is False
    assert program["production_policy_mutation_enabled"] is False
