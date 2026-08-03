#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

REPORT="examples/v02-release-qualification/v02-release-candidate-final-evaluation-report.json"

if [[ -f "$REPORT" ]]; then
  "$PYTHON_BIN" scripts/lib/v02_release_candidate_final_evaluation.py \
    check-report \
    --report "$REPORT"
else
  "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

root = Path.cwd()
path = root / "scripts/lib/v02_release_candidate_final_evaluation.py"
spec = importlib.util.spec_from_file_location("aion244_eval", path)
if spec is None or spec.loader is None:
    raise SystemExit("AION-244 evaluator cannot be loaded")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
if len(module.SCENARIO_IDS) != 32:
    raise SystemExit("AION-244 evaluator must define exactly 32 scenarios")
if len(set(module.SCENARIO_IDS)) != 32:
    raise SystemExit("AION-244 scenario IDs must be unique")
if module.PASS_DECISION != (
    "DETERMINISTIC_LOCAL_V02_RELEASE_CANDIDATE_FINAL_EVALUATION_PASS_AUTHORIZE_"
    "AION_V0_2_0_RC_1_ANNOTATED_TAG_AND_GITHUB_PRERELEASE_PUBLICATION"
):
    raise SystemExit("AION-244 PASS decision mismatch")
PY
  echo "AION-244 final evaluation harness skeleton PASS"
fi
