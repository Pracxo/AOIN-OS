from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT

APPLICATION_STATE = (
    "implemented_deterministic_operator_approved_non_factual_in_memory_shadow_only_"
    "pending_closeout"
)
PROGRAM_STATE = (
    "governed_learning_memory_engagement_application_implemented_shadow_only_"
    "pending_closeout"
)


def test_current_state_marks_engagement_application_authorized_after_local_persistence_closeout():
    ledger = json.loads(
        (REPO_ROOT / "docs/governed-learning-memory/program-ledger.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger["current_authorization"]["authorization_transaction_id"] == "AION-225-GLM-0003"
    assert ledger["current_authorization"]["authorized_task"] == "AION-226"
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


def test_aion226_current_state_implements_shadow_application_pending_closeout():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text())
    assert program["program_state"] == PROGRAM_STATE
    assert program["active_glm_implementation_authorization"] == "AION-225-GLM-0003"
    assert program["active_glm_implementation_task"] == "AION-226"
    assert program["formal_closeout_task"] == "AION-227"
    assert program["engagement_learning_application_authorized"] is True
    assert program["engagement_learning_application_implemented"] is True
    assert program["operator_invoked_engagement_shadow_application_available"] is True
    assert program["persistent_engagement_overlay_write_enabled"] is False
    assert program["aion_224_store_write_enabled"] is False
    assert program["production_policy_mutation_enabled"] is False
