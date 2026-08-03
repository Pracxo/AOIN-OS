#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    if payload.get("production_deployment_enabled", False) is not False:
        raise SystemExit(f"{relative} production deployment must remain false")
stable = subprocess.run(
    ["git", "tag", "--list", "aion-v0.2.0", "v0.2.0*"],
    cwd=root,
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
if stable:
    raise SystemExit(f"stable v0.2 tag exists: {stable}")
print("AION-244 RC1 publication authorization no-go PASS")
PY
