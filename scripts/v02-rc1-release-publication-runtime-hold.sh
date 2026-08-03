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
from pathlib import Path

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    for key in (
        "production_runtime_authorized",
        "production_deployment_enabled",
        "production_exposure",
        "registry_login_enabled",
        "registry_pull_enabled",
        "registry_push_enabled",
        "public_package_registry_upload_enabled",
        "production_credentials_enabled",
        "production_tokens_enabled",
        "production_database_enabled",
    ):
        if payload.get(key, False) is not False:
            raise SystemExit(f"{relative} runtime hold mismatch {key}: {payload.get(key)!r}")
print("AION-244 RC1 publication runtime hold PASS")
PY
