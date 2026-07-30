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

import os
import subprocess
from pathlib import Path
from typing import Any

import json

from governed_learning_memory_program_final_evaluation import EVALUATION_ID, PASS_DECISION

root = Path(os.environ["AION_REPO_ROOT"])
PRIMARY_BRANCH = "phase/governed-learning-memory-program-final-evaluation-closeout"
PRIMARY_PR = 146
PRIMARY_HARNESS_COMMIT = "1a45937f6fb5a25ffd468a6843f85f1b9a3bd0f1"
PRIMARY_CLOSEOUT_COMMIT = "3d718e29f07d260801bbe372c436442e95224d17"
PRIMARY_MERGE_COMMIT = "a6a6d62eb7c04666a206bfadbbcd640e5bdca10a"
PRIMARY_MERGED_AT = "2026-07-30T09:12:24Z"
RECONCILIATION_BRANCH = (
    "phase/governed-learning-memory-program-final-evidence-reconciliation"
)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_output(args: list[str]) -> str | None:
    result = _git(args)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _git_ancestor(candidate: str, ref: str) -> bool:
    return _git(["merge-base", "--is-ancestor", candidate, ref]).returncode == 0


def _gh_pr(payload_number: object | None) -> dict[str, Any] | None:
    if _git(["--version"]).returncode != 0:
        return None
    if subprocess.run(
        ["gh", "--version"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode != 0:
        return None

    fields = (
        "number,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,url"
    )
    if isinstance(payload_number, int):
        result = subprocess.run(
            ["gh", "pr", "view", str(payload_number), "--json", fields],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)

    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "all",
            "--base",
            "main",
            "--head",
            RECONCILIATION_BRANCH,
            "--json",
            fields,
            "--limit",
            "20",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    matches = json.loads(result.stdout)
    return matches[0] if matches else None


program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/governed-learning-memory/authorization-ledger.json").read_text(encoding="utf-8"))
delivery = program.get("aion_229_delivery", {})
reconciliation = delivery.get("evidence_reconciliation", {})

if program.get("program_state") != "governed_learning_memory_program_complete":
    raise SystemExit("program is not complete")
if program.get("governed_learning_memory_program_complete") is not True:
    raise SystemExit("program complete flag false")
if program.get("governed_learning_memory_program_evaluation_id") != EVALUATION_ID:
    raise SystemExit("final evaluation id mismatch")
if program.get("governed_learning_memory_program_evaluation_decision") != PASS_DECISION:
    raise SystemExit("final evaluation decision mismatch")
if auth.get("active_authorizations") != []:
    raise SystemExit("active authorizations remain")
for key in (
    "active_glm_implementation_authorization",
    "active_glm_implementation_task",
    "formal_closeout_task",
    "next_glm_implementation_authorization",
    "next_glm_implementation_task",
):
    if program.get(key) is not None or auth.get(key) is not None:
        raise SystemExit(f"pending field remains: {key}")
if program.get("final_completed_task") != "AION-229":
    raise SystemExit("final completed task mismatch")
required_delivery = {
    "task_id": "AION-229",
    "branch": PRIMARY_BRANCH,
    "ci_result": "pass",
    "evaluation_id": EVALUATION_ID,
    "evaluation_decision": PASS_DECISION,
    "authorization_transaction": None,
    "authorization_state": "no_active_glm_authorization",
    "next_task": None,
    "runtime_state": "governed_learning_memory_program_complete",
}
for key, value in required_delivery.items():
    if delivery.get(key) != value:
        raise SystemExit(f"AION-229 delivery mismatch {key}: {delivery.get(key)!r}")
expected_primary_delivery = {
    "harness_commit": PRIMARY_HARNESS_COMMIT,
    "closeout_commit": PRIMARY_CLOSEOUT_COMMIT,
    "feature_commits": [PRIMARY_HARNESS_COMMIT, PRIMARY_CLOSEOUT_COMMIT],
    "pull_requests": [PRIMARY_PR],
    "merge_commits": [PRIMARY_MERGE_COMMIT],
    "completion_timestamp": PRIMARY_MERGED_AT,
    "primary_pr": PRIMARY_PR,
    "primary_merge_commit": PRIMARY_MERGE_COMMIT,
    "primary_merged_at": PRIMARY_MERGED_AT,
    "evidence_reconciliation_required": False,
}
for key, value in expected_primary_delivery.items():
    if delivery.get(key) != value:
        raise SystemExit(f"AION-229 primary delivery mismatch {key}: {delivery.get(key)!r}")

expected_primary_reconciliation = {
    "primary_branch": PRIMARY_BRANCH,
    "primary_pr": PRIMARY_PR,
    "primary_feature_commits": [PRIMARY_HARNESS_COMMIT, PRIMARY_CLOSEOUT_COMMIT],
    "primary_merge_commit": PRIMARY_MERGE_COMMIT,
    "primary_merged_at": PRIMARY_MERGED_AT,
    "primary_ci_result": "pass",
}
for key, value in expected_primary_reconciliation.items():
    if reconciliation.get(key) != value:
        raise SystemExit(f"AION-229 reconciliation mismatch {key}: {reconciliation.get(key)!r}")

for sha in (PRIMARY_HARNESS_COMMIT, PRIMARY_CLOSEOUT_COMMIT, PRIMARY_MERGE_COMMIT):
    if not _git_ancestor(sha, "origin/main"):
        raise SystemExit(f"AION-229 primary commit is not in origin/main: {sha}")

head = _git_output(["rev-parse", "HEAD"])
origin = _git_output(["rev-parse", "origin/main"])
branch = _git_output(["branch", "--show-current"]) or ""
if not head or not origin:
    raise SystemExit("unable to resolve local HEAD and origin/main")

pending_branch_context = branch == RECONCILIATION_BRANCH or head != origin
if pending_branch_context:
    if reconciliation.get("state") != "pending_reconciliation_pr_merge":
        raise SystemExit("reconciliation branch must remain explicitly pending PR merge")
    for key in (
        "reconciliation_pr",
        "reconciliation_commit",
        "reconciliation_merge_commit",
        "reconciliation_merged_at",
        "final_main_sha",
        "final_origin_main_sha",
    ):
        if reconciliation.get(key) not in (None, ""):
            raise SystemExit(f"pre-merge reconciliation field must not be prefilled: {key}")
else:
    if head != origin:
        raise SystemExit("local HEAD is not origin/main")
    pr = _gh_pr(reconciliation.get("reconciliation_pr"))
    if not pr:
        raise SystemExit("AION-229 reconciliation PR could not be resolved")
    merge_commit = (pr.get("mergeCommit") or {}).get("oid")
    head_ref_oid = pr.get("headRefOid")
    if pr.get("state") != "MERGED":
        raise SystemExit("AION-229 reconciliation PR is not merged")
    if pr.get("baseRefName") != "main":
        raise SystemExit("AION-229 reconciliation PR base is not main")
    if pr.get("headRefName") != RECONCILIATION_BRANCH:
        raise SystemExit("AION-229 reconciliation PR head branch mismatch")
    if not pr.get("mergedAt"):
        raise SystemExit("AION-229 reconciliation merged timestamp missing")
    if not merge_commit or not _git_ancestor(merge_commit, "origin/main"):
        raise SystemExit("AION-229 reconciliation merge commit is not in origin/main")
    if not head_ref_oid or not _git_ancestor(head_ref_oid, "origin/main"):
        raise SystemExit("AION-229 reconciliation feature commit is not in origin/main")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "governed learning memory program final evidence reconciliation PASS"
