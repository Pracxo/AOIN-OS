#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/external-cognition-foundation-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__import__("os").environ["AION_REPO_ROOT"])
HARNESS = ROOT / "scripts/lib/external_cognition_foundation_operator_evaluation.py"
SAVED_REPORT = (
    ROOT
    / "examples/adaptive-intelligence/external-cognition-foundation-operator-evaluation-report.json"
)

spec = importlib.util.spec_from_file_location("aion247_external_cognition_eval", HARNESS)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load AION-247 evaluation harness")
harness = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness
spec.loader.exec_module(harness)

if SAVED_REPORT.exists():
    payload = json.loads(SAVED_REPORT.read_text(encoding="utf-8"))
    harness.validate_evaluation_report(payload)
    if payload["decision"] != harness.PASS_DECISION:
        raise SystemExit("AION-247 saved evaluation is not PASS")
    if payload["scenario_count"] != 32 or payload["hard_gate_count"] != 32:
        raise SystemExit("AION-247 saved evaluation scenario count mismatch")
else:
    tmp = Path("/tmp/aion-external-cognition-evaluation-check")
    if tmp.exists():
        shutil.rmtree(tmp)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report = tmp / "AION-ECGPE-001.json"
    code = harness.main(
        [
            "--repo-root",
            str(ROOT),
            "--evaluation-id",
            "AION-ECGPE-001",
            "--implementation-main-commit",
            "27d6ad15a043940bf537caec72cf7de7c74f6dc2",
            "--implementation-commit",
            "dd1f7b34cb2a25dfd409cf72667f073af9e8e965",
            "--pilot-evidence",
            "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json",
            "--evaluation-base-commit",
            base,
            "--temporary-output-directory",
            str(tmp),
            "--report",
            str(report),
        ]
    )
    if code != 0:
        raise SystemExit(code)
    harness.validate_evaluation_report(json.loads(report.read_text(encoding="utf-8")))
    shutil.rmtree(tmp)

print("external cognition foundation operator evaluation PASS")
PY
