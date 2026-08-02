#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/v02-staging-qualification-operator-evaluation-no-go-regression.sh >/dev/null

if git diff --name-only origin/main...HEAD -- 2>/dev/null | rg -n '^services/brain-api/src/aion_brain/(contracts/)?v02_release_candidate|^services/brain-api/src/aion_brain/v02_release_candidate/|^scripts/v02-release-candidate-local-run\.py$' >/dev/null 2>&1; then
  echo "AION-242 must not create AION-243 release-candidate source" >&2
  exit 1
fi
if git diff --name-only origin/main...HEAD -- 2>/dev/null | rg -n '(^|/)(pyproject\.toml|package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb)$' >/dev/null 2>&1; then
  echo "AION-242 must not change package versions or dependencies" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

import v02_staging_qualification_operator_evaluation as ev

root = Path.cwd()
for relative in ev.FUTURE_AION243_SOURCE_SCOPE:
    if (root / relative).exists():
        raise SystemExit(f"AION-243 source must be absent: {relative}")
if (root / ev.FUTURE_AION243_RUNNER).exists():
    raise SystemExit("AION-243 runner must be absent")
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
    "examples/v02-release-qualification/release-candidate-authorization.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    if payload.get("v02_release_ready") is not False:
        raise SystemExit(f"{relative} must keep v02_release_ready=false")
    if payload.get("v02_tag_created") is not False:
        raise SystemExit(f"{relative} must keep v02_tag_created=false")
    if payload.get("v02_release_created") is not False:
        raise SystemExit(f"{relative} must keep v02_release_created=false")
    if payload.get("release_candidate_created") is not False:
        raise SystemExit(f"{relative} must keep release_candidate_created=false")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "deterministic v0.2 release candidate artifact build authorization no-go PASS"
