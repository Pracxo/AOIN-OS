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

./scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh
REPORT_PATH="examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json"
"$PYTHON_BIN" -m json.tool "$REPORT_PATH" >/dev/null
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py --validate-report "$REPORT_PATH"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
ROOT = Path(os.environ["AION_REPO_ROOT"])
report = json.loads((ROOT / "examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json").read_text())
if report["decision"] != "INTEGRATED_RESEARCH_AGENT_OPERATOR_EVALUATION_PASS_RECOMMEND_VERIFIED_KNOWLEDGE_MEMORY_AUTHORIZATION":
    raise SystemExit("knowledge intelligence integrated research agent operator evaluation FAIL RECORDED")
if report["scenario_count"] != 28 or len(report["scenario_results"]) != 28:
    raise SystemExit("AION-IRAE-001 scenario count mismatch")
if any(item.get("passed") is not True for item in report["scenario_results"]):
    raise SystemExit("AION-IRAE-001 scenario failure")
if any(item.get("passed") is not True for item in report["hard_gate_results"]):
    raise SystemExit("AION-IRAE-001 hard gate failure")
if [item.get("plane_id") for item in report["plane_validation_results"]] != ["research_acquisition", "source_provenance_registry", "temporal_claim_evidence_graph", "epistemic_assessment", "domain_expert_mesh", "tool_verification_fabric"]:
    raise SystemExit("plane validation order mismatch")
for key in ("public_network_requests", "dns_resolutions", "search_provider_calls", "connector_calls", "model_provider_calls", "actual_tool_executions", "shell_executions", "subprocess_executions", "browser_actions", "filesystem_mutations", "source_mutations", "git_operations", "runtime_pull_requests", "runtime_approvals", "deployments", "model_weight_changes", "persistent_registry_writes", "persistent_graph_writes", "persistent_assessment_writes", "persistent_mesh_writes", "persistent_tool_state_writes", "persistent_verified_knowledge_writes", "automatic_knowledge_promotions", "cognitive_memory_writes", "belief_mutations", "engagement_fact_promotions", "engagement_confidence_effects"):
    if report.get(key) != 0:
        raise SystemExit(f"runtime effect is non-zero: {key}")
if report.get("repository_unchanged") is not True:
    raise SystemExit("repository unchanged proof missing")
for commit, label in (("c9a35cc853ee1587cb9e149a020e2f767ca80881", "feature"), ("2988b8f389f7ee3a141f74e351432f4ea79c6eae", "merge")):
    if subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT, check=False).returncode != 0:
        print(f"WARN: AION-215 {label} commit unavailable in this checkout; relying on report evidence")
        continue
    if not any(subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref], cwd=ROOT, check=False).returncode == 0 and subprocess.run(["git", "merge-base", "--is-ancestor", commit, ref], cwd=ROOT, check=False).returncode == 0 for ref in ("origin/main", "main", "HEAD")):
        raise SystemExit(f"AION-215 {label} commit is not in available main history: {commit}")
PY

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json, subprocess
from pathlib import Path
payload = json.loads(subprocess.run(["gh", "pr", "view", "129", "--json", "number,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName"], cwd=Path("."), capture_output=True, text=True, check=True).stdout)
assert payload["number"] == 129
assert payload["state"] == "MERGED"
assert payload["baseRefName"] == "main"
assert payload["headRefName"] == "phase/knowledge-intelligence-tool-verification-fabric"
assert payload["headRefOid"] == "c9a35cc853ee1587cb9e149a020e2f767ca80881"
assert payload["mergeCommit"]["oid"] == "2988b8f389f7ee3a141f74e351432f4ea79c6eae"
assert payload["mergedAt"] == "2026-07-26T08:49:51Z"
PY
else
  echo "WARN: gh authentication unavailable; PR #129 live check deferred to CI evidence"
fi

export AION_INTEGRATED_RESEARCH_AGENT_EVALUATION_RUNNING=1

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-tool-verification-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-tool-verification-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-domain-expert-mesh-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then echo "ERROR: v0.2 tag exists" >&2; exit 1; fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then echo "ERROR: v0.2 release exists" >&2; exit 1; fi
fi

echo "knowledge intelligence integrated research agent operator evaluation PASS"
