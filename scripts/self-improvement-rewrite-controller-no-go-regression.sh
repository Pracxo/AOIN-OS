#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

from aion_brain.self_improvement import (
    DisabledCIMonitorAdapter,
    DisabledMergeAdapter,
    DisabledPatchGenerator,
    DisabledPullRequestAdapter,
    DisabledSandboxRunner,
    GitController,
    MergeRequest,
    PatchRequest,
    PullRequestCreateRequest,
    required_sandbox_commands,
)


def expect_disabled(label: str, fn) -> None:
    try:
        fn()
    except RuntimeError:
        return
    raise AssertionError(f"{label} must be disabled by default")


patch_request = PatchRequest(
    proposal_id="proposal-172-no-go",
    base_sha="a" * 40,
    allowed_paths=("services/brain-api/tests/test_generated_regression.py",),
    regression_test_path="services/brain-api/tests/test_generated_regression.py",
    target_paths=("services/brain-api/tests/test_generated_regression.py",),
)
pr_request = PullRequestCreateRequest(
    proposal_id="proposal-172-no-go",
    branch_name="phase/self-improvement-approved-rewrite-controller",
    head_sha="a" * 40,
    diff_hash="d" * 64,
    title="AION-172 disabled PR creation check",
    body="Synthetic disabled-default check.",
)
merge_request = MergeRequest(
    proposal_id="proposal-172-no-go",
    pr_number=172,
    head_sha="a" * 40,
    approved_commit_sha="a" * 40,
    benchmark_fingerprint="b" * 64,
    approved_benchmark_fingerprint="b" * 64,
)

expect_disabled("patch generation", lambda: DisabledPatchGenerator().generate(patch_request))
expect_disabled(
    "sandbox execution",
    lambda: DisabledSandboxRunner().run(required_sandbox_commands()[0]),
)
expect_disabled(
    "pull request creation",
    lambda: DisabledPullRequestAdapter().create_pull_request(pr_request),
)
expect_disabled(
    "CI monitoring",
    lambda: DisabledCIMonitorAdapter().checks_for_pull_request(1, "a" * 40),
)
expect_disabled(
    "merge execution",
    lambda: DisabledMergeAdapter().merge_pull_request(merge_request),
)

try:
    GitController().reject_direct_main_push("HEAD:main")
except ValueError:
    pass
else:
    raise AssertionError("direct main push must be rejected")

print("self-improvement rewrite controller disabled-default checks PASS")
PY

echo "self-improvement rewrite controller no-go result:"
echo "- patch generation: disabled by default"
echo "- sandbox execution: disabled by default"
echo "- pull request creation: disabled by default"
echo "- CI monitoring: disabled by default"
echo "- merge execution: disabled by default"
echo "- direct main push: rejected"
echo "self-improvement rewrite controller no-go PASS"
