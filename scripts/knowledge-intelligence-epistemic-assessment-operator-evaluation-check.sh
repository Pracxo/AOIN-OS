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

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_INTEGRATED_RESEARCH_AGENT_EVALUATION_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json >/dev/null
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py \
  --validate-report examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json

"$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
PR_NUMBER = 123
FEATURE_COMMIT = "9a5bfca384a1720495cce677a817acef556f9e91"
MERGE_COMMIT = "737f166966aeacc2362fd62b852292264b3e2d97"
DECISION = (
    "EPISTEMIC_ASSESSMENT_ENGINE_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "DOMAIN_EXPERT_MESH_AUTHORIZATION"
)
ZERO_INTEGRITY_KEYS = (
    "source_body_bytes",
    "absolute_truth_decisions",
    "claim_true_assignments",
    "claim_false_assignments",
    "automatic_acceptances",
    "automatic_rejections",
    "contradiction_resolutions",
    "knowledge_promotions",
    "belief_creations",
    "belief_mutations",
    "persistent_writes",
    "network_calls",
    "model_provider_calls",
    "connector_calls",
    "tool_executions",
    "source_mutations",
    "git_operations",
    "runtime_pull_requests",
    "runtime_approvals",
    "runtime_merges",
    "deployments",
    "model_weight_changes",
)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def git_ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def verify_commit(commit: str, label: str) -> None:
    if run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], check=False).returncode != 0:
        print(f"WARN: AION-211 {label} commit unavailable in this checkout; relying on report evidence")
        return
    for candidate in ("origin/main", "main", "HEAD"):
        if git_ref_exists(candidate):
            result = run(["git", "merge-base", "--is-ancestor", commit, candidate], check=False)
            if result.returncode == 0:
                return
    raise SystemExit(f"AION-211 {label} commit is not in available main history: {commit}")


report = json.loads(
    (ROOT / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json").read_text()
)
if report["decision"] != DECISION or report["evaluation_passed"] is not True:
    raise SystemExit("AION-EAE-001 did not record the exact PASS decision")
if report["implementation_prs"] != [PR_NUMBER]:
    raise SystemExit("AION-211 PR evidence mismatch")
if report["implementation_feature_commits"] != [FEATURE_COMMIT]:
    raise SystemExit("AION-211 feature commit evidence mismatch")
if report["implementation_merge_commits"] != [MERGE_COMMIT]:
    raise SystemExit("AION-211 merge commit evidence mismatch")
if report["scenario_count"] != 28 or len(report["scenario_results"]) != 28:
    raise SystemExit("AION-EAE-001 scenario count mismatch")
if any(item.get("passed") is not True for item in report["scenario_results"]):
    raise SystemExit("AION-EAE-001 contains a failed scenario")
if any(item.get("passed") is not True for item in report["hard_gate_results"]):
    raise SystemExit("AION-EAE-001 contains a failed hard gate")
integrity = report["repository_integrity"]
for key in ZERO_INTEGRITY_KEYS:
    if integrity.get(key) != 0:
        raise SystemExit(f"repository integrity effect must remain zero: {key}")
if integrity.get("repository_unchanged") is not True:
    raise SystemExit("evaluation must not mutate the repository")
closeout = report["authorization_closeout"]
if closeout["authorization_transaction_id"] != "AION-210-KI-0004":
    raise SystemExit("AION-210 closeout ID mismatch")
if closeout["authorization_active"] is not False or closeout["authorization_consumed"] is not True:
    raise SystemExit("AION-210 closeout lifecycle mismatch")
if closeout["authorization_expired"] is not True or closeout["authorization_reusable"] is not False:
    raise SystemExit("AION-210 closeout must be expired and non-reusable")
next_auth = report["conditional_next_authorization"]
if next_auth["authorization_transaction_id"] != "AION-212-KI-0005":
    raise SystemExit("AION-212-KI-0005 next authorization missing")
if next_auth["implementation_task"] != "AION-213" or next_auth["formal_closeout_task"] != "AION-214":
    raise SystemExit("AION-213/AION-214 lineage mismatch")

verify_commit(FEATURE_COMMIT, "feature")
verify_commit(MERGE_COMMIT, "merge")
PYSCRIPT

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  "$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(".")
view = subprocess.run(
    [
        "gh",
        "pr",
        "view",
        "123",
        "--json",
        "number,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName",
    ],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=True,
)
payload = json.loads(view.stdout)
assert payload["number"] == 123
assert payload["state"] == "MERGED"
assert payload["baseRefName"] == "main"
assert payload["headRefName"] == "phase/knowledge-intelligence-epistemic-truth-engine"
assert payload["headRefOid"] == "9a5bfca384a1720495cce677a817acef556f9e91"
assert payload["mergeCommit"]["oid"] == "737f166966aeacc2362fd62b852292264b3e2d97"
assert payload["mergedAt"] == "2026-07-25T01:16:53Z"
checks = subprocess.run(
    ["gh", "pr", "checks", "123", "--json", "name,state,bucket"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=True,
)
required = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}
items = json.loads(checks.stdout)
states = {item["name"]: item for item in items}
missing = required - states.keys()
if missing:
    raise SystemExit(f"missing PR #123 checks: {sorted(missing)}")
failed = [
    (name, states[name].get("state"), states[name].get("bucket"))
    for name in sorted(required)
    if states[name].get("bucket") != "pass"
]
if failed:
    raise SystemExit(f"PR #123 checks not successful: {failed}")
PYSCRIPT
else
  echo "WARN: gh authentication unavailable; PR #123 live check deferred to external CI evidence"
fi

if is_nested_gate_context; then
  echo "PASS: inherited AION-211 downstream repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-epistemic-assessment-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

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

echo "knowledge intelligence epistemic assessment operator evaluation PASS"
