#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

REPORT="examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json"
test -f "$REPORT"
"$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_research_operator_evaluation.py --validate-report "$REPORT"

PR116_JSON="$(gh pr view 116 --json number,title,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,url)"
PR116_CHECKS_JSON="$(gh pr checks 116 --json name,state,bucket,workflow,link)"
PR117_JSON="$(gh pr view 117 --json number,title,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,url)"
PR117_CHECKS_JSON="$(gh pr checks 117 --json name,state,bucket,workflow,link)"

PR116_JSON="$PR116_JSON" PR116_CHECKS_JSON="$PR116_CHECKS_JSON" PR117_JSON="$PR117_JSON" PR117_CHECKS_JSON="$PR117_CHECKS_JSON" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

required = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}
pr = json.loads(os.environ["PR116_JSON"])
checks = json.loads(os.environ["PR116_CHECKS_JSON"])
corrective_pr = json.loads(os.environ["PR117_JSON"])
corrective_checks = json.loads(os.environ["PR117_CHECKS_JSON"])
report = json.loads(Path("examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json").read_text())
assert pr["number"] == 116
assert pr["state"] == "MERGED"
assert pr["baseRefName"] == "main"
assert pr["headRefName"] == "phase/knowledge-intelligence-research-acquisition-core"
assert pr["headRefOid"] == "b7299912f1c42c54581c20ad384602473169dcc1"
assert pr["mergeCommit"]["oid"] == "45d473fe2a07b62acd6f6957f5419fa78dcc6fc2"
assert pr["mergedAt"] == "2026-07-23T05:56:58Z"
states = {item["name"]: item["state"] for item in checks}
assert required <= states.keys()
for name in required:
    assert states[name] == "SUCCESS", name
assert corrective_pr["number"] == 117
assert corrective_pr["state"] == "MERGED"
assert corrective_pr["baseRefName"] == "main"
assert corrective_pr["headRefName"] == "phase/knowledge-intelligence-research-acquisition-core-evaluation-fix-1"
assert corrective_pr["headRefOid"] == "c06b54c8bcb969fcae98a421a5d088bdd2307c0b"
assert corrective_pr["mergeCommit"]["oid"] == "a775fb18bb0027d30834d8ab2507f461013753e2"
assert corrective_pr["mergedAt"] == "2026-07-23T10:13:46Z"
corrective_states = {item["name"]: item["state"] for item in corrective_checks}
assert required <= corrective_states.keys()
for name in required:
    assert corrective_states[name] == "SUCCESS", name
assert report["corrective_prs"] == [117]
assert report["implementation_feature_commits"] == [
    "b7299912f1c42c54581c20ad384602473169dcc1",
    "c06b54c8bcb969fcae98a421a5d088bdd2307c0b",
]
assert report["implementation_merge_commits"] == [
    "45d473fe2a07b62acd6f6957f5419fa78dcc6fc2",
    "a775fb18bb0027d30834d8ab2507f461013753e2",
]
assert report["scenario_count"] == 28
assert all(item["passed"] for item in report["scenario_results"])
assert all(report["hard_gate_results"].values())
assert report["repository_integrity"]["live_network_requests"] == 0
assert report["repository_integrity"]["live_dns_requests"] == 0
assert report["claim_verification_performed"] is False
assert report["knowledge_promoted"] is False
assert report["belief_mutated"] is False
PY

git merge-base --is-ancestor b7299912f1c42c54581c20ad384602473169dcc1 origin/main
git merge-base --is-ancestor 45d473fe2a07b62acd6f6957f5419fa78dcc6fc2 origin/main
git merge-base --is-ancestor c06b54c8bcb969fcae98a421a5d088bdd2307c0b origin/main
git merge-base --is-ancestor a775fb18bb0027d30834d8ab2507f461013753e2 origin/main

./scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-plane-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-plane-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/docs-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/final-docs-audit.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/verify-no-domain-drift.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/boundary-check.sh

decision="$("$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json").read_text())["decision"])
PY
)"

if [[ "$decision" == "RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION" ]]; then
  echo "knowledge intelligence research operator evaluation PASS"
else
  echo "knowledge intelligence research operator evaluation FAIL RECORDED"
fi
