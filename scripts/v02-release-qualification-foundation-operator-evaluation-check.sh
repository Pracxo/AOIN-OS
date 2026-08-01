#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

tmp_dir="${TMPDIR:-/tmp}/aion-v02rq-foundation-operator-evaluation-check"
if [[ -e "$tmp_dir" ]]; then
  rm -r "$tmp_dir"
fi
mkdir -m 700 "$tmp_dir"

./scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
  scripts/lib/v02_release_qualification_foundation_operator_evaluation.py \
  --repo-root "$ROOT_DIR" \
  --evaluation-id AION-V02RQPE-001 \
  --implementation-main-commit 154d58f182871ce18abad860f3bb76e5a006ebad \
  --evaluation-base-commit "$(git rev-parse HEAD)" \
  --pilot-evidence examples/v02-release-qualification/v02-production-readiness-qualification-foundation-pilot-evidence.json \
  --temporary-output-directory "$tmp_dir" \
  --report "$tmp_dir/AION-V02RQPE-001.json"

python3 -m json.tool "$tmp_dir/AION-V02RQPE-001.json" >/dev/null
PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
  scripts/lib/v02_release_qualification_foundation_operator_evaluation.py \
  --validate-report "$tmp_dir/AION-V02RQPE-001.json"

if [[ -f examples/v02-release-qualification/foundation-operator-evaluation-report.json ]]; then
  PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
    scripts/lib/v02_release_qualification_foundation_operator_evaluation.py \
    --validate-report examples/v02-release-qualification/foundation-operator-evaluation-report.json
  AION240_TMP_REPORT="$tmp_dir/AION-V02RQPE-001.json" \
  PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

generated = json.loads(Path(os.environ["AION240_TMP_REPORT"]).read_text(encoding="utf-8"))
committed = json.loads(Path("examples/v02-release-qualification/foundation-operator-evaluation-report.json").read_text(encoding="utf-8"))
for key in ("decision", "evaluation_passed", "scenario_count", "scenario_ids", "hard_gate_results"):
    if generated[key] != committed[key]:
        raise SystemExit(f"committed AION-240 evaluation report mismatch: {key}")
PY
fi

./scripts/v02-release-qualification-foundation-no-go-regression.sh >/dev/null
./scripts/v02-release-qualification-foundation-check.sh >/dev/null
./scripts/v02-release-qualification-foundation-pilot-evidence-check.sh >/dev/null
AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/v02-release-qualification-foundation-runtime-hold.sh >/dev/null

if [[ -e "$tmp_dir" ]]; then
  rm -r "$tmp_dir"
fi

echo "v0.2 release qualification foundation operator evaluation PASS"
