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
export AION_GLM_PROGRAM_AUTHORIZATION_CHECK_RUNNING=1

FINAL_MAIN="1acde151a2cf273e0998a3bda4a23716f74f2720"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        if [[ -n "$merge_base" ]]; then
          echo "$merge_base"
          return 0
        fi
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      if [[ -n "$merge_base" ]]; then
        echo "$merge_base"
        return 0
      fi
    fi
  done
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

require_ancestor() {
  local commit="$1"
  if git_ref_exists origin/main; then
    git merge-base --is-ancestor "$commit" origin/main
  else
    git merge-base --is-ancestor "$commit" HEAD
  fi
}

verify_pr_if_available() {
  local pr="$1"
  local expected_merge="$2"
  local expected_timestamp="$3"
  shift 3
  local expected_commits=("$@")
  local tmp_file

  if ! command -v gh >/dev/null 2>&1 || ! gh auth status -h github.com >/dev/null 2>&1; then
    echo "WARN: gh authenticated PR access unavailable; using committed AION-220 evidence for PR #${pr}" >&2
    return 0
  fi

  tmp_file="$(mktemp)"
  gh pr view "$pr" --repo Pracxo/AOIN-OS \
    --json number,state,mergedAt,mergeCommit,commits,statusCheckRollup > "$tmp_file"
  "$PYTHON_BIN" - "$tmp_file" "$pr" "$expected_merge" "$expected_timestamp" "${expected_commits[@]}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected_pr = int(sys.argv[2])
expected_merge = sys.argv[3]
expected_timestamp = sys.argv[4]
expected_commits = set(sys.argv[5:])
required_checks = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}
payload = json.loads(path.read_text(encoding="utf-8"))
if payload["number"] != expected_pr:
    raise SystemExit(f"PR number mismatch: {payload['number']}")
if payload["state"] != "MERGED":
    raise SystemExit(f"PR #{expected_pr} is not merged")
if payload["mergedAt"] != expected_timestamp:
    raise SystemExit(f"PR #{expected_pr} timestamp mismatch")
if payload["mergeCommit"]["oid"] != expected_merge:
    raise SystemExit(f"PR #{expected_pr} merge commit mismatch")
commits = {item["oid"] for item in payload["commits"]}
if expected_commits - commits:
    raise SystemExit(f"PR #{expected_pr} missing commits: {sorted(expected_commits - commits)}")
checks = {
    item["name"]: item.get("conclusion")
    for item in payload["statusCheckRollup"]
    if item.get("__typename") == "CheckRun"
}
missing = required_checks - checks.keys()
if missing:
    raise SystemExit(f"PR #{expected_pr} missing required checks: {sorted(missing)}")
bad = {name: checks[name] for name in required_checks if checks[name] != "SUCCESS"}
if bad:
    raise SystemExit(f"PR #{expected_pr} required check failure: {bad}")
PY
  rm -f "$tmp_file"
}

verify_pr_if_available \
  135 \
  2b2fbc471011cc080149c59ff99ace0300140a5c \
  2026-07-27T20:36:26Z \
  76b2e02adbbbcb2ef9c9a44f4ad30f1a3ebd7c7f \
  ccd3700d9dfd39cbb2bc56c811e6f38788e0f513

verify_pr_if_available \
  136 \
  "$FINAL_MAIN" \
  2026-07-27T21:08:27Z \
  808f71a5e0ced7aef124d30864c7c20feef03d79

for commit in \
  76b2e02adbbbcb2ef9c9a44f4ad30f1a3ebd7c7f \
  ccd3700d9dfd39cbb2bc56c811e6f38788e0f513 \
  2b2fbc471011cc080149c59ff99ace0300140a5c \
  808f71a5e0ced7aef124d30864c7c20feef03d79 \
  "$FINAL_MAIN"; do
  require_ancestor "$commit"
done

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-program-complete-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-program-complete-runtime-hold.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/governed-learning-memory/authorization-ledger.json").read_text(encoding="utf-8"))
ki_program = json.loads((root / "docs/knowledge-intelligence/program-ledger.json").read_text(encoding="utf-8"))
ki_auth = json.loads((root / "docs/knowledge-intelligence/authorization-ledger.json").read_text(encoding="utf-8"))
cognitive = json.loads((root / "docs/cognitive-architecture/program-ledger.json").read_text(encoding="utf-8"))
self_improvement = json.loads((root / "docs/self-improvement/program-ledger.json").read_text(encoding="utf-8"))

program_id = "AION-GOVERNED-LEARNING-MEMORY-001"
auth_id = "AION-221-GLM-0001"
scope = "verified-candidate-operator-approval-provenance-revalidation-deduplication-conflict-supersession-rollback-dry-run-cognitive-memory-projection-core"
decision = "CONTROLLED_PUBLIC_RESEARCH_PILOT_PASS_COMPLETE_KNOWLEDGE_INTELLIGENCE_PROGRAM"
required_program = {
    "program_id": program_id,
    "program_name": "AION Governed Learning and Memory Integration Program",
    "program_state": "governed_learning_memory_promotion_transaction_core_implemented_write_disabled_pending_closeout",
    "parent_program_ids": [
        "AION-COGNITIVE-ARCHITECTURE-001",
        "AION-KNOWLEDGE-INTELLIGENCE-001",
        "AION-SELF-IMPROVEMENT-001",
    ],
    "created_by_task": "AION-221",
    "final_planned_task": "AION-229",
    "active_glm_implementation_authorization_count": 1,
    "active_glm_implementation_authorization": auth_id,
    "active_glm_implementation_task": "AION-222",
    "formal_closeout_task": "AION-223",
    "new_program_created": True,
}
for label, payload in (("program", program), ("authorization", auth)):
    for key, expected in required_program.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{label} {key} mismatch: {payload.get(key)!r}")

expected_auth = {
    "authorization_transaction_id": auth_id,
    "approval_record_id": auth_id,
    "candidate_id": "approval-bound-knowledge-promotion-transaction-core",
    "workstream": "governed-learning-memory-integration",
    "implementation_task": "AION-222",
    "formal_closeout_task": "AION-223",
    "authorization_scope": scope,
    "authorization_transaction_approved": True,
    "explicit_approval_record_approval": True,
    "implementation_authorization_approved": True,
    "implementation_go_status": True,
    "implementation_no_go_status": False,
    "authorization_active": True,
    "authorization_consumed": False,
    "authorization_expired": False,
    "authorization_reusable": False,
    "parent_knowledge_program_id": "AION-KNOWLEDGE-INTELLIGENCE-001",
    "parent_knowledge_program_closeout_task": "AION-220",
    "parent_knowledge_program_evaluation_id": "AION-KIPE-001",
    "parent_knowledge_program_decision": decision,
    "parent_cognitive_program_id": "AION-COGNITIVE-ARCHITECTURE-001",
    "parent_self_improvement_program_id": "AION-SELF-IMPROVEMENT-001",
}
for key, expected in expected_auth.items():
    if auth.get(key) != expected:
        raise SystemExit(f"authorization {key} mismatch: {auth.get(key)!r}")

for key, value in auth["authorized_capabilities"].items():
    if value is not True:
        raise SystemExit(f"authorized capability not true: {key}")
for key, value in auth["prohibited_capabilities"].items():
    if value is not False:
        raise SystemExit(f"prohibited capability not false: {key}")

required_limits = {
    "maximum_promotion_requests_per_batch": 100,
    "maximum_candidates_per_request": 100,
    "maximum_lineage_references_per_candidate": 500,
    "maximum_source_references_per_candidate": 100,
    "maximum_claim_references_per_candidate": 20,
    "maximum_assessment_references_per_candidate": 20,
    "maximum_mesh_references_per_candidate": 20,
    "maximum_tool_session_references_per_candidate": 20,
    "maximum_approval_evidence_records_per_transaction": 4,
    "maximum_projection_records_per_transaction": 100,
    "maximum_versions_per_knowledge_identity": 100,
    "maximum_rollback_steps_per_transaction": 50,
    "maximum_compensation_steps_per_transaction": 50,
    "maximum_operator_review_items": 100,
    "maximum_in_memory_transactions": 1000,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrency": 4,
    "maximum_persistent_knowledge_writes": 0,
    "maximum_persistent_verified_knowledge_writes": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_semantic_memory_writes": 0,
    "maximum_episodic_memory_writes": 0,
    "maximum_procedural_memory_writes": 0,
    "maximum_belief_creations": 0,
    "maximum_belief_mutations": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_engagement_fact_promotions": 0,
    "maximum_engagement_confidence_effects": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
if auth["resource_limits"] != required_limits:
    raise SystemExit("resource limit mismatch")

for source_path in auth["authorized_source_scope"]:
    if not (root / source_path).exists():
        raise SystemExit(f"AION-222 source missing after implementation: {source_path}")

if ki_program["program_state"] != "knowledge_intelligence_program_complete":
    raise SystemExit("Knowledge Intelligence program not complete")
if ki_auth["active_knowledge_implementation_authorization_count"] != 0:
    raise SystemExit("Knowledge Intelligence active authorization count is not zero")
if any(item.get("authorization_active") is True for item in ki_auth["records"]):
    raise SystemExit("active Knowledge Intelligence authorization record remains")
if cognitive["active_cognitive_implementation_authorization_count"] != 0:
    raise SystemExit("Cognitive Architecture active authorization count is not zero")
if self_improvement["active_self_improvement_implementation_authorization"] != "none":
    raise SystemExit("Self-Improvement active authorization is not none")
PY

base_ref="$(comparison_base || true)"
if [[ -n "$base_ref" ]]; then
  changed_source="$(git diff --name-only --diff-filter=ACMRT "$base_ref" HEAD -- services/brain-api/src/aion_brain || true)"
  allowed_source="$("$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

root = Path.cwd()
auth = json.loads((root / "docs/governed-learning-memory/authorization-ledger.json").read_text(encoding="utf-8"))
print("\n".join(auth["authorized_source_scope"]))
PY
)"
  if [[ -n "$changed_source" ]]; then
    while IFS= read -r path; do
      [[ -n "$path" ]] || continue
      if ! grep -Fxq "$path" <<<"$allowed_source"; then
        echo "ERROR: runtime source outside AION-222 authorization changed: $path" >&2
        exit 1
      fi
    done <<<"$changed_source"
  fi
fi

for path in \
  services/brain-api/src/aion_brain/contracts/governed_learning_memory.py \
  services/brain-api/src/aion_brain/governed_learning_memory/__init__.py \
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py \
  services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py \
  services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py \
  services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py \
  services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py \
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py \
  services/brain-api/src/aion_brain/governed_learning_memory/rollback.py \
  services/brain-api/src/aion_brain/governed_learning_memory/integrity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/evidence.py; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: AION-222 source missing after implementation: $path" >&2
    exit 1
  fi
done

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
aion_confirm_immutable_v01_tag_history >/dev/null

echo "governed learning memory program authorization PASS"
