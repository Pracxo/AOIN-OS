from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
VERIFIED_KNOWLEDGE_MEMORY_STATE = (
    "implemented_deterministic_in_memory_candidate_versioning_engagement_learning_"
    "persistent_write_disabled"
)
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def _active_record(ledger: dict[str, object]) -> dict[str, object]:
    active = [
        item
        for item in ledger["records"]
        if isinstance(item, dict) and item.get("authorization_active") is True
    ]
    assert len(active) == 1
    return active[0]


def test_current_projection_matches_active_public_pilot_authorization() -> None:
    auth_ledger = _load_json("docs/knowledge-intelligence/authorization-ledger.json")
    program_ledger = _load_json("docs/knowledge-intelligence/program-ledger.json")
    if program_ledger["program_state"] == "knowledge_intelligence_program_complete":
        assert [
            item
            for item in auth_ledger["records"]
            if isinstance(item, dict) and item.get("authorization_active") is True
        ] == []
        for ledger in (auth_ledger, program_ledger):
            assert ledger["active_knowledge_implementation_authorization_count"] == 0
            assert ledger["active_knowledge_implementation_authorization"] is None
            assert ledger["active_knowledge_implementation_task"] is None
            assert ledger["formal_closeout_task"] is None
            assert ledger["verified_knowledge_memory_authorized"] is True
            assert ledger["verified_knowledge_memory_implemented"] is True
            assert ledger["controlled_public_research_pilot_authorized"] is True
            assert ledger["controlled_public_research_pilot_implemented"] is True
            assert ledger["controlled_public_research_pilot_passed"] is True
            assert ledger["public_network_fetch_enabled"] is False
            assert ledger["verified_knowledge_runtime_enabled"] is False
            assert ledger["persistent_verified_knowledge_write_enabled"] is False
            assert ledger["automatic_verified_knowledge_promotion_enabled"] is False
        return

    active = _active_record(auth_ledger)
    for relative in (
        "docs/knowledge-intelligence/authorization-ledger.json",
        "docs/knowledge-intelligence/program-ledger.json",
    ):
        ledger = _load_json(relative)
        assert ledger["authorization_transaction_id"] == active["authorization_transaction_id"]
        assert ledger["candidate_id"] == active["candidate_id"]
        assert ledger["workstream"] == active["workstream"]
        assert ledger["implementation_task"] == active["implementation_task"]
        assert ledger["formal_closeout_task"] == active["formal_closeout_task"]
        assert ledger["active_knowledge_implementation_authorization"] == "AION-218-KI-0008"
        assert ledger["active_knowledge_implementation_task"] == "AION-219"
        assert ledger["formal_closeout_task"] == "AION-220"
        assert ledger["verified_knowledge_memory_authorized"] is True
        assert ledger["verified_knowledge_memory_implemented"] is True
        assert ledger["verified_knowledge_memory_state"] == VERIFIED_KNOWLEDGE_MEMORY_STATE
        assert ledger["engagement_learning_candidate_plane_authorized"] is True
        assert ledger["engagement_learning_candidate_plane_implemented"] is True
        assert ledger["controlled_public_research_pilot_authorized"] is True
        assert ledger["controlled_public_research_pilot_implemented"] is True
        assert ledger["operator_invoked_public_https_fetch_available"] is True
        assert ledger["system_dns_resolution_available"] is True
        assert ledger["system_http_transport_available"] is True
        assert ledger["public_network_fetch_enabled"] is False
        assert ledger["verified_knowledge_runtime_enabled"] is False
        assert ledger["persistent_verified_knowledge_write_enabled"] is False
        assert ledger["automatic_verified_knowledge_promotion_enabled"] is False


def test_aion_214_authorization_is_closed_after_integrated_evaluation() -> None:
    ledger = _load_json("docs/knowledge-intelligence/authorization-ledger.json")
    closed = [
        item
        for item in ledger["records"]
        if isinstance(item, dict) and item.get("authorization_transaction_id") == "AION-214-KI-0006"
    ]
    assert len(closed) == 1
    assert closed[0]["authorization_active"] is False
    assert closed[0]["authorization_consumed"] is True
    assert closed[0]["authorization_expired"] is True
    assert closed[0]["authorization_reusable"] is False
    assert closed[0]["authorization_closed_by_task"] == "AION-216"
