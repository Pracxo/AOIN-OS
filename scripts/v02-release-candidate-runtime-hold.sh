#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

import v02_staging_qualification_operator_evaluation as ev

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
    "examples/v02-release-qualification/release-candidate-authorization.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    if payload.get("release_candidate_artifact_build_authorized") is not True:
        raise SystemExit(f"{relative} must authorize release-candidate build")
    if payload.get("release_candidate_artifact_build_implemented") is not False:
        raise SystemExit(f"{relative} must keep release-candidate build unimplemented")
    for key in (
        "release_candidate_created",
        "release_candidate_published",
        "production_runtime_authorized",
        "production_deployment_enabled",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"{relative} runtime hold mismatch {key}: {payload.get(key)!r}")
for relative in ev.FUTURE_AION243_SOURCE_SCOPE:
    if (root / relative).exists():
        raise SystemExit(f"AION-243 source exists before implementation: {relative}")
if (root / ev.FUTURE_AION243_RUNNER).exists():
    raise SystemExit("AION-243 local runner exists before implementation")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "deterministic v0.2 release candidate artifact build runtime hold PASS"
