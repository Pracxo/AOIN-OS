#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

tmp_dir="${TMPDIR:-/tmp}/aion-v02-staging-operator-evaluation-check"
if [[ -e "$tmp_dir" ]]; then
  rm -r "$tmp_dir"
fi
mkdir -m 700 "$tmp_dir"

./scripts/v02-staging-qualification-operator-evaluation-no-go-regression.sh

if [[ -f examples/v02-release-qualification/v02-release-candidate-final-evaluation-report.json ]]; then
  PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
    scripts/lib/v02_staging_qualification_operator_evaluation.py \
    --validate-report examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json
  ./scripts/v02-staging-qualification-no-go-regression.sh >/dev/null
  ./scripts/v02-staging-qualification-check.sh >/dev/null
  ./scripts/v02-staging-qualification-pilot-evidence-check.sh >/dev/null
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/v02-staging-qualification-runtime-hold.sh >/dev/null
  if [[ -e "$tmp_dir" ]]; then
    rm -r "$tmp_dir"
  fi
  echo "controlled isolated staging qualification operator evaluation PASS"
  exit 0
fi

AION242_REQUIRE_LOCAL_DOCKER="${AION242_REQUIRE_LOCAL_DOCKER:-1}" \
PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
  scripts/lib/v02_staging_qualification_operator_evaluation.py \
  --repo-root "$ROOT_DIR" \
  --evaluation-id AION-V02RQPE-002 \
  --implementation-main-commit 24095a3fabe95b59f2607134199d160e8122e343 \
  --evaluation-base-commit "$(git rev-parse HEAD)" \
  --pilot-evidence examples/v02-release-qualification/v02-controlled-isolated-staging-pilot-evidence.json \
  --temporary-output-directory "$tmp_dir" \
  --report "$tmp_dir/AION-V02RQPE-002.json"

python3 -m json.tool "$tmp_dir/AION-V02RQPE-002.json" >/dev/null
PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
  scripts/lib/v02_staging_qualification_operator_evaluation.py \
  --validate-report "$tmp_dir/AION-V02RQPE-002.json"

if [[ -f examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json ]]; then
  PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" \
    scripts/lib/v02_staging_qualification_operator_evaluation.py \
    --validate-report examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json
  AION242_TMP_REPORT="$tmp_dir/AION-V02RQPE-002.json" \
  PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

generated = json.loads(Path(os.environ["AION242_TMP_REPORT"]).read_text(encoding="utf-8"))
committed = json.loads(Path("examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json").read_text(encoding="utf-8"))
for key in ("decision", "evaluation_passed", "scenario_count", "scenario_ids", "hard_gate_results"):
    if generated[key] != committed[key]:
        raise SystemExit(f"committed AION-242 evaluation report mismatch: {key}")
PY
fi

if [[ -f examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json ]]; then
  ./scripts/v02-staging-qualification-no-go-regression.sh >/dev/null
  ./scripts/v02-staging-qualification-check.sh >/dev/null
  ./scripts/v02-staging-qualification-pilot-evidence-check.sh >/dev/null
  AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/v02-staging-qualification-runtime-hold.sh >/dev/null
fi

if [[ -e "$tmp_dir" ]]; then
  rm -r "$tmp_dir"
fi

echo "controlled isolated staging qualification operator evaluation PASS"
