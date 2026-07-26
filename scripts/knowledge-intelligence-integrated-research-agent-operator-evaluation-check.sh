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
if [[ -f "$REPORT_PATH" ]]; then
  "$PYTHON_BIN" -m json.tool "$REPORT_PATH" >/dev/null
  "$PYTHON_BIN" scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py \
    --validate-report "$REPORT_PATH"
else
  TMP_DIR="${TMPDIR:-/tmp}/aion-integrated-research-agent-evaluation-check"
  rm -rf "$TMP_DIR"
  mkdir -p "$TMP_DIR"
  "$PYTHON_BIN" scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py \
    --repo-root "$ROOT_DIR" \
    --evaluation-id AION-IRAE-001 \
    --evaluation-base-commit "$(git rev-parse HEAD)" \
    --temporary-output-directory "$TMP_DIR" \
    --report "$TMP_DIR/AION-IRAE-001.json"
  "$PYTHON_BIN" -m json.tool "$TMP_DIR/AION-IRAE-001.json" >/dev/null
  "$PYTHON_BIN" scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py \
    --validate-report "$TMP_DIR/AION-IRAE-001.json"
  rm -rf "$TMP_DIR"
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(".")
FEATURE_COMMIT = "c9a35cc853ee1587cb9e149a020e2f767ca80881"
MERGE_COMMIT = "2988b8f389f7ee3a141f74e351432f4ea79c6eae"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def git_ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def verify_commit(commit: str, label: str) -> None:
    if run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], check=False).returncode != 0:
        print(f"WARN: AION-215 {label} commit unavailable in this checkout; relying on report evidence")
        return
    for candidate in ("origin/main", "main", "HEAD"):
        if git_ref_exists(candidate) and run(
            ["git", "merge-base", "--is-ancestor", commit, candidate],
            check=False,
        ).returncode == 0:
            return
    raise SystemExit(f"AION-215 {label} commit is not in available main history: {commit}")


verify_commit(FEATURE_COMMIT, "feature")
verify_commit(MERGE_COMMIT, "merge")

report_path = ROOT / "examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json"
if report_path.exists():
    report = json.loads(report_path.read_text())
    if report["evaluation_id"] != "AION-IRAE-001":
        raise SystemExit("AION-IRAE-001 report missing")
    if report["scenario_count"] != 28 or len(report["scenario_results"]) != 28:
        raise SystemExit("AION-IRAE-001 scenario count mismatch")
    if report["implementation_prs"] != [129]:
        raise SystemExit("AION-215 PR evidence mismatch")
    if report["implementation_feature_commits"] != [FEATURE_COMMIT]:
        raise SystemExit("AION-215 feature commit evidence mismatch")
    if report["implementation_merge_commits"] != [MERGE_COMMIT]:
        raise SystemExit("AION-215 merge commit evidence mismatch")
PY

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  "$PYTHON_BIN" - <<'PY'
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
        "129",
        "--json",
        "number,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName",
    ],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=True,
)
payload = json.loads(view.stdout)
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

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence integrated research agent operator evaluation PASS"
