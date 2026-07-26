"""AION-216 verified-knowledge authorization evidence validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knowledge_intelligence_integrated_research_agent_operator_evaluation import (
    AUTHORIZED_CAPABILITIES,
    DECISION_PASS,
    NEXT_AUTHORIZATION_ID,
    PROHIBITED_CAPABILITIES,
    VERIFIED_KNOWLEDGE_RESOURCE_LIMITS,
    validate_evaluation_report,
)

PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
CURRENT_AUTHORIZATION_ID = "AION-214-KI-0006"
AUTHORIZATION_ID = "AION-216-KI-0007"
EVALUATION_ID = "AION-IRAE-001"
IMPLEMENTATION_TASK = "AION-217"
FORMAL_CLOSEOUT_TASK = "AION-218"
CANDIDATE_ID = "verified-knowledge-memory-engagement-learning-core"
WORKSTREAM = "knowledge-intelligence-verified-knowledge-memory"
SCOPE = "deterministic-verified-knowledge-candidate-lineage-versioning-revalidation-operator-review-engagement-learning-abstention-core"
PROGRAM_STATE = "verified_knowledge_memory_authorized_not_implemented"
IMPLEMENTED_PROGRAM_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
VERIFIED_KNOWLEDGE_MEMORY_STATE = (
    "implemented_deterministic_in_memory_candidate_versioning_engagement_learning_"
    "persistent_write_disabled"
)
ENGAGEMENT_LEARNING_CANDIDATE_PLANE_STATE = (
    "implemented_deterministic_in_memory_non_factual_candidate_only"
)
AION217_SOURCE_PATHS = (
    "services/brain-api/src/aion_brain/contracts/knowledge_verified_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_lineage.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_versioning.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_revalidation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_signal_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_evidence.py",
)
AION217_OPTIONAL_SOURCE_PATHS = (
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
)
ENGAGEMENT_SIGNAL_KINDS = ("query_repeated", "response_accepted", "response_rejected", "correction_submitted", "citation_opened", "follow_up_requested", "retrieval_succeeded", "retrieval_failed", "clarification_requested", "task_outcome_reported")
ENGAGEMENT_LEARNING_CANDIDATE_KINDS = ("research_gap", "clarification_need", "retrieval_strategy", "source_selection", "domain_routing", "verification_rule", "tool_manifest_gap", "response_quality", "preference_candidate")
ELIGIBILITY_STATUSES = ("eligible_for_operator_review", "ineligible_insufficient_evidence", "ineligible_low_confidence", "ineligible_incomplete_provenance", "ineligible_incomplete_citations", "ineligible_stale", "ineligible_retracted", "ineligible_superseded", "ineligible_scope_mismatch", "ineligible_unresolved_contradiction", "ineligible_material_dissent", "ineligible_integrity_failure", "revalidation_required", "abstained")

def load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))

def expected_authorized_capabilities() -> dict[str, bool]:
    return {key: True for key in AUTHORIZED_CAPABILITIES}

def expected_prohibited_capabilities() -> dict[str, bool]:
    return {key: False for key in PROHIBITED_CAPABILITIES}

def validate_authorization_payload(payload: dict[str, Any]) -> None:
    expected = {"program_id": PROGRAM_ID, "authorization_transaction_id": AUTHORIZATION_ID, "approval_record_id": AUTHORIZATION_ID, "parent_authorization_transaction_id": CURRENT_AUTHORIZATION_ID, "parent_evaluation_id": EVALUATION_ID, "parent_evaluation_decision": DECISION_PASS, "candidate_id": CANDIDATE_ID, "workstream": WORKSTREAM, "implementation_task": IMPLEMENTATION_TASK, "formal_closeout_task": FORMAL_CLOSEOUT_TASK, "authorization_scope": SCOPE, "authorization_active": True, "authorization_consumed": False, "authorization_expired": False, "authorization_reusable": False, "active_knowledge_implementation_authorization_count": 1, "active_cognitive_implementation_authorization_count": 0, "synthetic": True, "read_only": True, "redacted": True, "runtime_effect": False}
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"verified-knowledge authorization mismatch {key}: {payload.get(key)!r}")
    for key in ("authorization_transaction_approved", "explicit_approval_record_approval", "implementation_authorization_approved", "implementation_go_status"):
        if payload.get(key) is not True:
            raise ValueError(f"authorization flag must be true: {key}")
    if payload.get("implementation_no_go_status") is not False:
        raise ValueError("implementation_no_go_status must be false")
    if payload.get("authorized_capabilities") != expected_authorized_capabilities():
        raise ValueError("authorized capabilities mismatch")
    if payload.get("prohibited_capabilities") != expected_prohibited_capabilities():
        raise ValueError("prohibited capabilities mismatch")
    if payload.get("resource_limits") != VERIFIED_KNOWLEDGE_RESOURCE_LIMITS:
        raise ValueError("resource limits mismatch")

def is_implemented_state(payload: dict[str, Any]) -> bool:
    return payload.get("program_state") == IMPLEMENTED_PROGRAM_STATE

def validate_implemented_state(label: str, payload: dict[str, Any]) -> None:
    if payload.get("program_state") not in {PROGRAM_STATE, IMPLEMENTED_PROGRAM_STATE}:
        raise ValueError(f"{label} program state mismatch")
    if is_implemented_state(payload):
        expected = {
            "verified_knowledge_memory_authorized": True,
            "verified_knowledge_memory_implemented": True,
            "engagement_learning_candidate_plane_authorized": True,
            "engagement_learning_candidate_plane_implemented": True,
        }
        for key, value in expected.items():
            if payload.get(key) is not value:
                raise ValueError(f"{label} implemented flag mismatch: {key}")
        if payload.get("verified_knowledge_memory_state") != VERIFIED_KNOWLEDGE_MEMORY_STATE:
            raise ValueError(f"{label} verified knowledge memory state mismatch")
        if (
            payload.get("engagement_learning_candidate_plane_state")
            != ENGAGEMENT_LEARNING_CANDIDATE_PLANE_STATE
        ):
            raise ValueError(f"{label} engagement learning plane state mismatch")
    else:
        if payload.get("verified_knowledge_memory_implemented") is not False:
            raise ValueError(f"{label} verified knowledge memory must be unimplemented")
        if payload.get("engagement_learning_candidate_plane_implemented") is not False:
            raise ValueError(f"{label} engagement learning plane must be unimplemented")

def validate_report(root: Path) -> dict[str, Any]:
    report = load_json(root, "examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json")
    validate_evaluation_report(report)
    if report.get("decision") != DECISION_PASS or report.get("evaluation_passed") is not True:
        raise ValueError("AION-IRAE-001 exact PASS report is required")
    if report.get("scenario_count") != 28 or len(report.get("scenario_results", [])) != 28:
        raise ValueError("AION-IRAE-001 scenario count mismatch")
    if any(item.get("passed") is not True for item in report.get("hard_gate_results", [])):
        raise ValueError("AION-IRAE-001 hard gate failure recorded")
    return report

def validate_authorization_files(root: Path) -> None:
    report = validate_report(root)
    authorization = load_json(root, "examples/knowledge-intelligence/verified-knowledge-authorization.json")
    validate_authorization_payload(authorization)
    if authorization.get("parent_main_commit") != "2988b8f389f7ee3a141f74e351432f4ea79c6eae":
        raise ValueError("parent main commit mismatch")
    closeout = report["authorization_closeout"]
    for key, value in {"authorization_transaction_id": CURRENT_AUTHORIZATION_ID, "authorization_active": False, "authorization_consumed": True, "authorization_expired": True, "authorization_reusable": False, "authorization_closed_by_task": "AION-216", "authorization_consumed_by_task": "AION-215"}.items():
        if closeout.get(key) != value:
            raise ValueError(f"AION-214 closeout mismatch {key}")
    if closeout.get("authorization_consumed_by_prs") != [129]:
        raise ValueError("AION-214 closeout PR evidence mismatch")
    auth_ledger = load_json(root, "docs/knowledge-intelligence/authorization-ledger.json")
    program_ledger = load_json(root, "docs/knowledge-intelligence/program-ledger.json")
    for label, payload in (("authorization", auth_ledger), ("program", program_ledger)):
        validate_implemented_state(label, payload)
        if payload.get("active_knowledge_implementation_authorization") != AUTHORIZATION_ID:
            raise ValueError(f"{label} active authorization mismatch")
        if payload.get("active_knowledge_implementation_authorization_count") != 1:
            raise ValueError(f"{label} active authorization count mismatch")
        if payload.get("active_knowledge_implementation_task") != IMPLEMENTATION_TASK:
            raise ValueError(f"{label} active task mismatch")
        if payload.get("formal_closeout_task") != FORMAL_CLOSEOUT_TASK:
            raise ValueError(f"{label} formal closeout mismatch")
        for key in ("verified_knowledge_runtime_enabled", "persistent_verified_knowledge_write_enabled", "automatic_verified_knowledge_promotion_enabled", "cognitive_memory_write_enabled", "belief_mutation_enabled", "engagement_signal_as_fact_enabled", "engagement_confidence_effect_enabled", "public_network_fetch_enabled", "actual_tool_execution_enabled"):
            if payload.get(key) is not False:
                raise ValueError(f"{label} runtime boundary enabled: {key}")
    records = auth_ledger["records"]
    active = [item for item in records if item.get("authorization_active") is True]
    if len(active) != 1:
        raise ValueError("exactly one active Knowledge Intelligence authorization is required")
    validate_authorization_payload(active[0])
    closed = [item for item in records if item.get("authorization_transaction_id") == CURRENT_AUTHORIZATION_ID]
    if len(closed) != 1:
        raise ValueError("AION-214-KI-0006 closeout record missing")
    if closed[0].get("authorization_active") is not False or closed[0].get("authorization_consumed") is not True:
        raise ValueError("AION-214-KI-0006 is not closed")
    validate_repository_state(root, implemented=is_implemented_state(program_ledger))

def validate_runtime_hold(root: Path) -> None:
    validate_authorization_files(root)
    runtime = load_json(root, "examples/knowledge-intelligence/verified-knowledge-runtime-hold.json")
    if runtime.get("verified_knowledge_memory_implemented") is not True:
        raise ValueError("verified knowledge memory must be implemented in runtime hold")
    if runtime.get("engagement_learning_candidate_plane_implemented") is not True:
        raise ValueError("engagement learning plane must be implemented in runtime hold")
    if runtime.get("verified_knowledge_memory_state") != VERIFIED_KNOWLEDGE_MEMORY_STATE:
        raise ValueError("runtime hold verified knowledge memory state mismatch")
    for key in ("verified_knowledge_runtime_enabled", "persistent_verified_knowledge_write_enabled", "verified_knowledge_database_enabled", "automatic_verified_knowledge_promotion_enabled", "automatic_candidate_approval_enabled", "cognitive_memory_write_enabled", "belief_mutation_enabled", "engagement_signal_as_fact_enabled", "engagement_confidence_effect_enabled", "public_network_fetch_enabled", "actual_tool_execution_enabled", "background_verified_knowledge_worker_enabled", "scheduled_revalidation_job_enabled", "runtime_effect"):
        if runtime.get(key) is not False:
            raise ValueError(f"runtime hold flag must remain false: {key}")
    if runtime.get("verified_knowledge_memory_authorized") is not True:
        raise ValueError("verified knowledge authorization missing from runtime hold")

def validate_repository_state(root: Path, *, implemented: bool) -> None:
    for relative in AION217_SOURCE_PATHS:
        exists = (root / relative).exists()
        if implemented and not exists:
            raise ValueError(f"AION-217 source missing: {relative}")
        if not implemented and exists:
            raise ValueError(f"AION-217 source is not allowed before implementation: {relative}")
    forbidden = (
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/cognitive_memory_writer.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_policy_updater.py",
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
    )
    for relative in forbidden:
        if (root / relative).exists():
            raise ValueError(f"forbidden AION-217 runtime path exists: {relative}")
    for evidence_root in ("docs", "examples", "operator-console-static", "scripts"):
        for path in (root / evidence_root).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".jsonl", ".state"}:
                raise ValueError(f"tracked state file detected: {path.relative_to(root)}")
