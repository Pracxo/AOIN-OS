#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.self_improvement import (
    CANARY_RUNTIME_ENABLED,
    PRODUCTION_EXPOSURE_ENABLED,
    DisabledCIMonitorAdapter,
    DisabledGitCommandRunner,
    DisabledMergeAdapter,
    DisabledPatchGenerator,
    DisabledPullRequestAdapter,
    DisabledSandboxRunner,
    MergeRequest,
    PatchRequest,
    PullRequestCreateRequest,
    SandboxCommand,
)

ROOT = Path.cwd()
AUTHORIZATION = json.loads((ROOT / "docs/self-improvement/authorization-ledger.json").read_text())
REPORT = json.loads((ROOT / "examples/self-improvement/final-readiness-report.json").read_text())

FALSE_KEYS = {
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "automatic_merge_enabled",
    "automatic_production_deployment_enabled",
    "source_rewriting_enabled",
    "source_mutation_enabled",
    "git_commits_enabled",
    "branch_creation_enabled",
    "pull_request_creation_enabled",
    "merge_enabled",
    "automatic_approval_enabled",
    "benchmark_mutation_by_candidate_enabled",
    "holdout_disclosure_to_patch_generators_enabled",
    "production_deployment_enabled",
    "deployment_enabled",
    "model_weight_training_enabled",
    "model_weight_changes_enabled",
    "canary_runtime_enabled",
    "production_canary_enabled",
    "production_exposure_enabled",
    "unrestricted_traffic_exposure_enabled",
    "automatic_protected_core_modification_enabled",
    "automatic_policy_relaxation_enabled",
    "runtime_self_approval_enabled",
    "autonomous_production_activation_enabled",
}

TRUE_KEYS = {
    "self_improvement_platform_implemented",
    "proposal_generation_available",
    "experiment_execution_available",
    "benchmark_comparison_available",
    "isolated_worktree_available",
    "test_first_patch_generation_available",
    "approval_bound_pr_creation_available",
    "approval_bound_merge_control_available",
    "canary_simulation_available",
    "automatic_rollback_available",
    "adaptive_retrieval_candidates_available",
    "case_based_planning_candidates_available",
    "procedural_skill_candidates_available",
    "human_approval_required",
    "exact_commit_approval_required",
    "exact_diff_hash_approval_required",
    "no_self_approval",
    "protected_core_dual_approval_required",
    "holdout_protected",
    "rollback_required",
}

active_authorizations = [
    record for record in AUTHORIZATION["records"] if record.get("authorization_active") is True
]
if active_authorizations:
    raise SystemExit("self-improvement authorization must not remain active")

final_record = AUTHORIZATION["records"][-1]
if final_record["authorization_transaction_id"] != "AION-173-SI-0005":
    raise SystemExit("final authorization closeout id mismatch")
if final_record["authorization_consumed_by_task"] != "AION-174":
    raise SystemExit("AION-173-SI-0005 must be consumed by AION-174")
if final_record["authorization_consumed_by_pr"] != 85:
    raise SystemExit("AION-173-SI-0005 must be consumed by PR 85")
if final_record["self_improvement_platform_state"] != "implemented_disabled":
    raise SystemExit("platform state must be implemented_disabled")

runtime_state = REPORT["runtime_state"]
approval_state = REPORT["approval_state"]
security_gates = REPORT["security_gates"]
if runtime_state["self_improvement_platform_state"] != "implemented_disabled":
    raise SystemExit("readiness report platform state must be implemented_disabled")
if approval_state["authorization_active"] is not False:
    raise SystemExit("readiness report authorization_active must be false")
if approval_state["new_implementation_authorization_created"] is not False:
    raise SystemExit("AION-175 must not create a new implementation authorization")

for key in FALSE_KEYS:
    if final_record.get(key) is not False:
        raise SystemExit(f"authorization ledger {key} must be false")
for key in TRUE_KEYS:
    if final_record.get(key) is not True:
        raise SystemExit(f"authorization ledger {key} must be true")
for key in {
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
}:
    if runtime_state.get(key) is not False:
        raise SystemExit(f"readiness report {key} must be false")
for key in {
    "direct_main_writes",
    "self_approval",
    "automatic_merge",
    "production_deployment",
    "production_canary",
    "protected_core_ordinary_modification",
    "benchmark_self_modification",
    "holdout_disclosure",
    "test_weakening_allowed",
    "runtime_self_rewrite",
    "model_weight_training",
    "v02_tag_created",
    "v02_release_created",
}:
    if security_gates.get(key) is not False:
        raise SystemExit(f"readiness report security gate {key} must be false")
if security_gates["aion_v010_unchanged"] is not True:
    raise SystemExit("aion-v0.1.0 unchanged proof must be true")
if CANARY_RUNTIME_ENABLED is not False or PRODUCTION_EXPOSURE_ENABLED is not False:
    raise SystemExit("canary runtime constants must remain false")


def expect_runtime_disabled(label: str, fn) -> None:
    try:
        fn()
    except RuntimeError:
        return
    raise SystemExit(f"{label} must be disabled")


patch_request = PatchRequest(
    proposal_id="proposal-175-hold",
    base_sha="a" * 40,
    allowed_paths=("services/brain-api/tests/test_self_improvement_final_closeout_docs.py",),
    regression_test_path="services/brain-api/tests/test_self_improvement_final_closeout_docs.py",
    target_paths=("services/brain-api/tests/test_self_improvement_final_closeout_docs.py",),
)
pr_request = PullRequestCreateRequest(
    proposal_id="proposal-175-hold",
    branch_name="phase/self-improvement-final-closeout",
    head_sha="b" * 40,
    diff_hash="c" * 64,
    title="AION-175 synthetic disabled PR request",
    body="Synthetic request used only to verify disabled runtime defaults.",
)
merge_request = MergeRequest(
    proposal_id="proposal-175-hold",
    pr_number=175,
    head_sha="b" * 40,
    approved_commit_sha="b" * 40,
    benchmark_fingerprint="d" * 64,
    approved_benchmark_fingerprint="d" * 64,
)
sandbox_command = SandboxCommand(gate_name="focused_tests", command=("pytest", "-q"))

expect_runtime_disabled("patch generation", lambda: DisabledPatchGenerator().generate(patch_request))
expect_runtime_disabled("sandbox execution", lambda: DisabledSandboxRunner().run(sandbox_command))
expect_runtime_disabled(
    "pull request creation",
    lambda: DisabledPullRequestAdapter().create_pull_request(pr_request),
)
expect_runtime_disabled("merge", lambda: DisabledMergeAdapter().merge_pull_request(merge_request))
expect_runtime_disabled(
    "CI monitoring",
    lambda: DisabledCIMonitorAdapter().checks_for_pull_request(175, "b" * 40),
)
expect_runtime_disabled(
    "local Git command execution",
    lambda: DisabledGitCommandRunner().run_git(ROOT, ("status", "--short")),
)

print("self-improvement runtime hold disabled-default checks PASS")
PY

# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

cat <<'SUMMARY'
self-improvement runtime hold result:
- self_improvement_platform_state=implemented_disabled
- active implementation authorization=false
- self_improvement_runtime_enabled=false
- self_rewrite_runtime_enabled=false
- automatic_merge_enabled=false
- production_canary_enabled=false
- production_deployment_enabled=false
- model_weight_training_enabled=false
- disabled adapters: patch, sandbox, PR, CI, merge, and local Git execution
self-improvement runtime hold PASS
SUMMARY
