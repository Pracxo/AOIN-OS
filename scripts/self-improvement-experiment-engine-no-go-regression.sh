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
    DisabledExperimentCandidateProvider,
    DisabledHypothesisGenerator,
    DisabledRegressionTestProposalGenerator,
    ImprovementProposalService,
)

service = ImprovementProposalService()
assert isinstance(service._hypothesis_generator, DisabledHypothesisGenerator)
assert isinstance(service._regression_test_generator, DisabledRegressionTestProposalGenerator)
assert isinstance(
    service._experiment_runner._candidate_provider,
    DisabledExperimentCandidateProvider,
)

for flag in (
    "source_modified",
    "git_branch_created",
    "pr_created",
    "runtime_effect",
):
    assert flag

print("self-improvement experiment engine disabled-default checks PASS")
PY

echo "self-improvement experiment engine no-go PASS"
