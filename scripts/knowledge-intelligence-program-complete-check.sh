#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json
import os
from pathlib import Path
from knowledge_intelligence_program_final_evaluation import (
    AUTHORIZATION_ID,
    EVALUATION_ID,
    PASS_DECISION,
    SCENARIO_IDS,
    validate_evaluation_report,
)

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((root / "docs/knowledge-intelligence/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/knowledge-intelligence/authorization-ledger.json").read_text(encoding="utf-8"))
report = json.loads((root / "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json").read_text(encoding="utf-8"))
validate_evaluation_report(report)
required = {
    "program_state": "knowledge_intelligence_program_complete",
    "knowledge_intelligence_program_complete": True,
    "knowledge_intelligence_program_evaluation_id": EVALUATION_ID,
    "knowledge_intelligence_program_evaluation_decision": PASS_DECISION,
    "controlled_public_research_pilot_passed": True,
    "active_knowledge_implementation_authorization_count": 0,
    "active_knowledge_implementation_authorization": None,
    "active_knowledge_implementation_task": None,
    "formal_closeout_task": None,
    "new_knowledge_implementation_authorization_created": False,
    "next_knowledge_implementation_authorization": None,
    "next_knowledge_implementation_task": None,
    "v02_release_ready": False,
}
for label, payload in (("program", program), ("authorization", auth)):
    for key, value in required.items():
        if payload.get(key) != value:
            raise SystemExit(f"{label} mismatch {key}: {payload.get(key)!r}")
    for key in (
        "public_network_fetch_enabled",
        "unrestricted_network_access_enabled",
        "background_network_access_enabled",
        "scheduled_public_research_enabled",
        "background_crawler_enabled",
        "automatic_verified_knowledge_promotion_enabled",
        "persistent_verified_knowledge_write_enabled",
        "cognitive_memory_write_enabled",
        "belief_mutation_enabled",
        "production_exposure",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"{label} prohibited flag enabled: {key}")
closed = next(item for item in auth["records"] if item.get("authorization_transaction_id") == AUTHORIZATION_ID)
if closed.get("authorization_active") is not False:
    raise SystemExit("AION-218-KI-0008 active after closeout")
if closed.get("authorization_consumed") is not True:
    raise SystemExit("AION-218-KI-0008 not consumed")
if closed.get("authorization_expired") is not True:
    raise SystemExit("AION-218-KI-0008 not expired")
if closed.get("authorization_reusable") is not False:
    raise SystemExit("AION-218-KI-0008 became reusable")
if closed.get("authorization_closed_by_task") != "AION-220":
    raise SystemExit("AION-218-KI-0008 not closed by AION-220")
if any(item.get("authorization_active") is True for item in auth["records"]):
    raise SystemExit("active Knowledge Intelligence authorization remains")
if report["scenario_count"] != len(SCENARIO_IDS):
    raise SystemExit("scenario count mismatch")
if report["program_completion_state"]["final_planned_task"] != "AION-220":
    raise SystemExit("final planned task mismatch")
if set(item["plane_id"] for item in report["plane_validation_results"]) != {
    "controlled_research_acquisition",
    "source_provenance_registry",
    "temporal_claim_evidence_graph",
    "epistemic_assessment_engine",
    "domain_expert_mesh",
    "tool_verification_fabric",
    "verified_knowledge_candidate_memory",
    "controlled_public_https_research_pilot",
}:
    raise SystemExit("architecture plane coverage mismatch")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence program complete PASS"
