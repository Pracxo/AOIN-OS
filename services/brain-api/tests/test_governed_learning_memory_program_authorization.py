from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227
from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION223_AUTHORIZATION_ID,
    AION224_APPROVED_CAPABILITIES,
    AION224_AUTHORIZATION_SCOPE,
    AION224_PROHIBITED_CAPABILITIES,
    AION224_TASK,
    AION225_TASK,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    FINAL_GLM_PROGRAM_STATES,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
    PASS_DECISION,
    PROGRAM_ID,
    validate_authorization_ledgers,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AUTH_ID = AION223_AUTHORIZATION_ID
CANDIDATE_ID = "operator-approved-local-append-only-knowledge-persistence-core"
WORKSTREAM = "governed-learning-memory-local-persistence"
IMPLEMENTATION_TASK = AION224_TASK
FORMAL_CLOSEOUT_TASK = AION225_TASK
SCOPE = AION224_AUTHORIZATION_SCOPE
KI_DECISION = "CONTROLLED_PUBLIC_RESEARCH_PILOT_PASS_COMPLETE_KNOWLEDGE_INTELLIGENCE_PROGRAM"
AUTHORIZED_CAPABILITIES = set(AION224_APPROVED_CAPABILITIES)
PROHIBITED_CAPABILITIES = set(AION224_PROHIBITED_CAPABILITIES)


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aion_223_program_and_authorization_are_exact() -> None:
    program, auth = validate_authorization_ledgers(REPO_ROOT)
    for payload in (program, auth):
        assert payload["program_id"] == PROGRAM_ID
        assert payload["program_state"] in {
            IMPLEMENTED_PENDING_CLOSEOUT_STATE,
            ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
            ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
            auth227.PROGRAM_STATE,
            *FINAL_GLM_PROGRAM_STATES,
        }
        if payload["program_state"] in {
            ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
            ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
        }:
            assert payload["active_glm_implementation_authorization_count"] == 1
            assert payload["active_glm_implementation_authorization"] == "AION-225-GLM-0003"
            assert payload["active_glm_implementation_task"] == "AION-226"
            assert payload["formal_closeout_task"] == "AION-227"
        elif payload["program_state"] == auth227.PROGRAM_STATE:
            assert payload["active_glm_implementation_authorization_count"] == 1
            assert payload["active_glm_implementation_authorization"] == "AION-227-GLM-0004"
            assert payload["active_glm_implementation_task"] == "AION-228"
            assert payload["formal_closeout_task"] == "AION-229"
        elif payload["program_state"] in FINAL_GLM_PROGRAM_STATES:
            assert payload["active_glm_implementation_authorization_count"] == 0
            assert payload["active_glm_implementation_authorization"] is None
            assert payload["active_glm_implementation_task"] is None
        else:
            assert payload["active_glm_implementation_authorization_count"] == 1
            assert payload["active_glm_implementation_authorization"] == AUTH_ID
            assert payload["active_glm_implementation_task"] == IMPLEMENTATION_TASK
            assert payload["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
        assert payload["promotion_transaction_operator_evaluation_decision"] == PASS_DECISION
        assert payload["local_append_only_knowledge_store_authorized"] is True
        assert payload["local_append_only_knowledge_store_implemented"] is True
        assert payload["operator_invoked_local_persistence_available"] is True
        assert payload["synthetic_local_persistence_pilot_completed"] is True
        assert payload["runtime_enabled"] is False
        assert payload["production_persistent_knowledge_write_enabled"] is False
        assert payload["automatic_knowledge_promotion_enabled"] is False
    if auth["program_state"] in {
        ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
        ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    }:
        assert auth["authorization_transaction_id"] == "AION-225-GLM-0003"
        assert auth["implementation_task"] == "AION-226"
        record = next(
            item
            for item in auth["records"]
            if item["authorization_transaction_id"] == AUTH_ID
        )
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-225"
    elif auth["program_state"] in {auth227.PROGRAM_STATE, *FINAL_GLM_PROGRAM_STATES}:
        assert auth["authorization_transaction_id"] == "AION-227-GLM-0004"
        assert auth["implementation_task"] == "AION-228"
        if auth["program_state"] == auth227.PROGRAM_STATE:
            assert auth["formal_closeout_task"] == "AION-229"
        else:
            assert auth["authorization_active"] is False
            assert auth["authorization_consumed"] is True
            assert auth["authorization_expired"] is True
            assert auth["authorization_closed_by_task"] == "AION-229"
        record = next(
            item
            for item in auth["records"]
            if item["authorization_transaction_id"] == "AION-225-GLM-0003"
        )
        assert record["authorization_active"] is False
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_reusable"] is False
        assert record["authorization_closed_by_task"] == "AION-227"
    else:
        assert auth["authorization_transaction_id"] == AUTH_ID
        assert auth["approval_record_id"] == AUTH_ID
        assert auth["candidate_id"] == CANDIDATE_ID
        assert auth["workstream"] == WORKSTREAM
        assert auth["implementation_task"] == IMPLEMENTATION_TASK
        assert auth["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
        assert auth["authorization_scope"] == SCOPE
        assert auth["authorization_active"] is True
        assert auth["authorization_consumed"] is False
        assert auth["authorization_expired"] is False
        assert auth["authorization_reusable"] is False


def test_authorized_and_prohibited_capabilities_are_explicit() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    if auth["program_state"] in {auth227.PROGRAM_STATE, *FINAL_GLM_PROGRAM_STATES}:
        authorized = set(auth227.AUTHORIZED_CAPABILITIES)
        prohibited = set(auth227.PROHIBITED_CAPABILITIES)
    else:
        authorized = AUTHORIZED_CAPABILITIES
        prohibited = PROHIBITED_CAPABILITIES
    assert set(auth["authorized_capabilities"]) == authorized
    assert set(auth["prohibited_capabilities"]) == prohibited
    assert all(auth["authorized_capabilities"][k] is True for k in authorized)
    assert all(auth["prohibited_capabilities"][k] is False for k in prohibited)
