#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/v02-release-candidate-evidence-check.sh >/dev/null

if [[ "${AION_RELEASE_CANDIDATE_LIVE_RETENTION:-0}" != "1" ]]; then
  echo "deterministic v0.2 release candidate retention evidence-only PASS"
  exit 0
fi

"$PYTHON_BIN" scripts/v02-release-candidate-local-run.py verify-candidate \
  --candidate-root "$HOME/.aion/release-candidates/aion-v0.2.0-rc.1" >/dev/null

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c

root = Path.cwd()
evidence = json.loads(
    (root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json").read_text(
        encoding="utf-8"
    )
)
image_id = subprocess.run(
    ["docker", "image", "inspect", "--format", "{{.Id}}", c.LOCAL_IMAGE_TAG],
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
if image_id != evidence["candidate_image_id"]:
    raise SystemExit("retained candidate image ID does not match committed evidence")
if subprocess.run(
    ["docker", "image", "inspect", "--format", "{{.Id}}", c.COMPARISON_IMAGE_TAG],
    capture_output=True,
    text=True,
    check=False,
).returncode == 0:
    raise SystemExit("comparison candidate image must not be retained")
PY

echo "deterministic v0.2 release candidate live retention PASS"
