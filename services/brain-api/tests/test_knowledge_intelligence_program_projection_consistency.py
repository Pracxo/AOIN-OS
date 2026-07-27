from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FINAL_STATUS_MARKER = (
    "AION-220 final Knowledge Intelligence Program evaluation and closeout complete"
)
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
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


def test_program_and_authorization_ledgers_match_active_public_pilot_authorization() -> None:
    auth_ledger = _load_json("docs/knowledge-intelligence/authorization-ledger.json")
    program_ledger = _load_json("docs/knowledge-intelligence/program-ledger.json")
    expected_memory_state = (
        "implemented_deterministic_in_memory_candidate_versioning_"
        "engagement_learning_persistent_write_disabled"
    )
    active_records = [
        record for record in auth_ledger["records"] if record.get("authorization_active") is True
    ]
    if program_ledger.get("program_state") == "knowledge_intelligence_program_complete":
        assert active_records == []
        for ledger in (auth_ledger, program_ledger):
            assert ledger["active_knowledge_implementation_authorization_count"] == 0
            assert ledger["active_knowledge_implementation_authorization"] is None
            assert ledger["active_knowledge_implementation_task"] is None
            assert ledger["formal_closeout_task"] is None
            assert ledger["new_knowledge_implementation_authorization_created"] is False
            assert ledger["next_knowledge_implementation_authorization"] is None
            assert ledger["next_knowledge_implementation_task"] is None
            assert ledger["controlled_public_research_pilot_implemented"] is True
            assert ledger["controlled_public_research_pilot_passed"] is True
            assert ledger["public_network_fetch_enabled"] is False
            assert ledger["verified_knowledge_runtime_enabled"] is False
            assert ledger["persistent_verified_knowledge_write_enabled"] is False
            assert ledger["engagement_signal_as_fact_enabled"] is False
        records = {
            record["task_id"]: record
            for record in program_ledger["records"]
            if "task_id" in record
        }
        assert records["AION-219"]["authorization_transaction"] == "AION-218-KI-0008"
        assert records["AION-220"]["evaluation_id"] == "AION-KIPE-001"
        return

    assert len(active_records) == 1
    active = active_records[0]
    for ledger in (auth_ledger, program_ledger):
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
        assert ledger["verified_knowledge_memory_state"] == expected_memory_state
        assert ledger["controlled_public_research_pilot_authorized"] is True
        assert ledger["controlled_public_research_pilot_implemented"] is True
        assert ledger["operator_invoked_public_https_fetch_available"] is True
        assert ledger["system_dns_resolution_available"] is True
        assert ledger["system_http_transport_available"] is True
        assert ledger["public_network_fetch_enabled"] is False
        assert ledger["verified_knowledge_runtime_enabled"] is False
        assert ledger["persistent_verified_knowledge_write_enabled"] is False
        assert ledger["engagement_signal_as_fact_enabled"] is False
    records = {
        record["task_id"]: record for record in program_ledger["records"] if "task_id" in record
    }
    assert records["AION-213"]["authorization_state"] == "consumed_by_AION-213_closed_by_AION-214"
    assert records["AION-214"]["pull_requests"] == [128]
    assert records["AION-215"]["pull_requests"] == [129]
    assert records["AION-216"]["authorization_transaction"] == "AION-216-KI-0007"
    assert records["AION-217"]["authorization_transaction"] == "AION-216-KI-0007"
    assert records["AION-218"]["authorization_transaction"] == "AION-218-KI-0008"


def test_project_status_current_projection_matches_ledgers_and_keeps_history() -> None:
    status = (REPO_ROOT / "docs/project-status.md").read_text(encoding="utf-8")
    if "knowledge_intelligence_program_complete=true" in status:
        assert FINAL_STATUS_MARKER in status
        assert "active_knowledge_implementation_authorization_count=0" in status
        assert "active_knowledge_implementation_authorization=null" in status
        assert "next_knowledge_implementation_task=null" in status
        assert "v02_release_ready=false" in status
        assert "Historical marker" in status
        assert "AION-214 domain expert mesh operator evaluation complete" in status
        return

    assert "AION-218 verified-knowledge memory operator evaluation complete" in status
    assert "active_knowledge_implementation_authorization=AION-218-KI-0008" in status
    assert "active_knowledge_implementation_task=AION-219" in status
    assert "formal_closeout_task=AION-220" in status
    assert "Historical marker" in status
    assert "AION-214 domain expert mesh operator evaluation complete" in status
