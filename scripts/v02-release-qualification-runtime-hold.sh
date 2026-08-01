#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads(
    (root / "docs/v02-release-qualification/program-ledger.json").read_text(
        encoding="utf-8"
    )
)
auth = json.loads(
    (root / "docs/v02-release-qualification/authorization-ledger.json").read_text(
        encoding="utf-8"
    )
)
required_false = (
    "production_auth_runtime_enabled",
    "external_identity_provider_call_enabled",
    "credential_generation_enabled",
    "credential_read_enabled",
    "credential_persistence_enabled",
    "token_generation_enabled",
    "token_read_enabled",
    "token_persistence_enabled",
    "live_replay_ledger_enabled",
    "staging_deployment_enabled",
    "production_deployment_enabled",
    "deployment_execution_enabled",
    "production_observability_export_enabled",
    "v02_release_candidate_created",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)
for label, payload in (("program", program), ("authorization", auth)):
    if payload.get("v02_release_qualification_program_authorized") is not True:
        raise SystemExit(f"{label} qualification program is not authorized")
    if payload.get("v02_release_qualification_program_implemented") is not True:
        raise SystemExit(f"{label} qualification program is not implemented")
    if payload.get("v02_release_qualification_foundation_implemented") is not True:
        raise SystemExit(f"{label} qualification foundation is not implemented")
    if payload.get("v02_release_qualification_foundation_state") != (
        "implemented_disabled_design_and_local_simulation_pending_AION-240_closeout"
    ):
        raise SystemExit(f"{label} qualification foundation state mismatch")
    if payload.get("local_qualification_pilot_completed") is not True:
        raise SystemExit(f"{label} local qualification pilot is not complete")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{label} runtime hold mismatch {key}: {payload.get(key)!r}")
    prohibited = payload.get("prohibited_capabilities", {})
    for key in required_false:
        if key in prohibited and prohibited[key] is not False:
            raise SystemExit(f"{label} prohibited capability enabled: {key}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "v0.2 release qualification runtime hold PASS"
