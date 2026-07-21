#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

REPORT="examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json"
test -f "$REPORT" || {
  echo "missing AION-182 report: $REPORT" >&2
  exit 1
}

"$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/shadow-activation-control-plane-evaluation-scenario-summary.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/actual-shadow-activation-review-boundary.json >/dev/null
"$PYTHON_BIN" -m json.tool operator-console-static/demo-data/self-improvement-shadow-activation-control-plane-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool operator-console-static/demo-data/self-improvement-actual-shadow-activation-review-boundary.json >/dev/null
"$PYTHON_BIN" scripts/lib/self_improvement_shadow_activation_operator_evaluation.py \
  --validate-report "$REPORT"

git merge-base --is-ancestor c7c7a5c83606399dff2221bd7f847ea00e177603 origin/main
git merge-base --is-ancestor e9374853a53cd098096ed50da0fabb5874152d54 origin/main

PR92_JSON="$(gh pr view 92 --json number,title,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,url)"
PR92_CHECKS_JSON="$(gh pr checks 92 --json name,state,bucket,workflow,link)"
POLICY_ATTEMPT1_JSON="$(gh api repos/Pracxo/AOIN-OS/actions/runs/29775002751/attempts/1/jobs)"
POLICY_ATTEMPT2_JSON="$(gh api repos/Pracxo/AOIN-OS/actions/runs/29775002751/attempts/2/jobs)"

PR92_JSON="$PR92_JSON" \
PR92_CHECKS_JSON="$PR92_CHECKS_JSON" \
POLICY_ATTEMPT1_JSON="$POLICY_ATTEMPT1_JSON" \
POLICY_ATTEMPT2_JSON="$POLICY_ATTEMPT2_JSON" \
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

required_checks = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}

pr = json.loads(os.environ["PR92_JSON"])
checks = json.loads(os.environ["PR92_CHECKS_JSON"])
attempt1 = json.loads(os.environ["POLICY_ATTEMPT1_JSON"])
attempt2 = json.loads(os.environ["POLICY_ATTEMPT2_JSON"])
report = json.loads(Path("examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json").read_text())
ledger = json.loads(Path("docs/self-improvement/authorization-ledger.json").read_text())
program = json.loads(Path("docs/self-improvement/program-ledger.json").read_text())

assert pr["number"] == 92
assert pr["state"] == "MERGED"
assert pr["baseRefName"] == "main"
assert pr["headRefName"] == "phase/self-improvement-shadow-activation-control-plane"
assert pr["headRefOid"] == "c7c7a5c83606399dff2221bd7f847ea00e177603"
assert pr["mergeCommit"]["oid"] == "e9374853a53cd098096ed50da0fabb5874152d54"
assert pr["mergedAt"] == "2026-07-20T21:10:45Z"

states = {item["name"]: item for item in checks}
assert required_checks <= states.keys()
for name in required_checks:
    assert states[name]["state"] == "SUCCESS", name

first_jobs = attempt1.get("jobs", [])
second_jobs = attempt2.get("jobs", [])
assert any(job.get("name") == "policy-check" and job.get("conclusion") == "cancelled" for job in first_jobs)
assert any(job.get("name") == "policy-check" and job.get("conclusion") == "success" for job in second_jobs)

assert ledger["active_self_improvement_implementation_authorization_count"] == 0
assert ledger["active_self_improvement_implementation_authorization"] == "none"
assert ledger["active_implementation_task"] == "none"
assert ledger["new_implementation_authorization_created"] is False
record = [
    item for item in ledger["records"]
    if item.get("authorization_transaction_id") == "AION-180-SI-0007"
][0]
assert record["authorization_active"] is False
assert record["authorization_consumed"] is True
assert record["authorization_consumed_by_task"] == "AION-181"
assert record["authorization_consumed_by_pr"] == 92
assert record["authorization_expired"] is True
assert record["authorization_reusable"] is False
assert record["control_plane_operator_evaluation_id"] == "AION-SACE-001"
assert record["control_plane_operator_evaluation_decision"] == report["decision"]
assert record["control_plane_operator_evaluation_used_as_approval"] is False

for item in program["records"]:
    if item.get("task_id") == "AION-181":
        aion181 = item
        break
else:
    raise AssertionError("AION-181 program record missing")
assert aion181["feature_commits"] == ["c7c7a5c83606399dff2221bd7f847ea00e177603"]
assert aion181["pull_requests"] == [92]
assert aion181["merge_commits"] == ["e9374853a53cd098096ed50da0fabb5874152d54"]
assert aion181["ci_result"] == "pass"
assert aion181["authorization_state"] == "consumed_by_AION-181_closed_by_AION-182"

assert report["decision"] == "SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW"
assert report["scenario_count"] == 21
assert all(item["passed"] for item in report["scenario_results"])
assert all(report["hard_gate_results"].values())
integrity = report["repository_integrity"]
assert integrity["canonical_repository_untouched_by_evaluation"] is True
assert integrity["control_plane_real_pull_request_created"] is False
assert integrity["control_plane_git_operation_count"] == 0
assert integrity["control_plane_source_mutation_count"] == 0
assert integrity["control_plane_network_call_count"] == 0
assert integrity["control_plane_connector_call_count"] == 0
assert integrity["control_plane_provider_call_count"] == 0
assert integrity["control_plane_approval_creation_count"] == 0
assert integrity["control_plane_runtime_promotion_count"] == 0
for key in (
    "new_implementation_authorization_created",
    "activation_approval_created",
    "actual_activation_created",
    "shadow_activation_enabled",
    "source_modified",
    "git_mutated",
    "pull_request_created",
    "merged",
    "runtime_effect",
    "active_learning_promoted",
    "production_exposure",
):
    assert report[key] is False, key
PY

./scripts/self-improvement-shadow-activation-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-operator-evaluation

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_self_improvement_shadow_activation_operator_evaluation.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_operator_evaluation_docs.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_authorization_closeout.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_no_runtime_effect.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-control-plane-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-control-plane-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/docs-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/final-docs-audit.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/verify-no-domain-drift.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/boundary-check.sh

decision="$("$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json").read_text())
print(payload["decision"])
PY
)"

if [[ "$decision" == "SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW" ]]; then
  echo "self improvement shadow activation operator evaluation PASS"
else
  echo "self improvement shadow activation operator evaluation FAIL RECORDED"
fi
