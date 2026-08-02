#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

changed_paths() {
  git diff --name-only --diff-filter=ACMRT origin/main...HEAD -- 2>/dev/null || true
  git diff --name-only --diff-filter=ACMRT HEAD --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard --
}

aion243_implementation_context() {
  changed_paths | sort -u | rg -q \
    '^(docs/adr/0207-deterministic-local-v02-release-candidate-artifact-bundle-build-and-retention\.md|docs/release/v02-release-candidate-|docs/v02-release-qualification/(aion-243-checklist|release-candidate-)|examples/v02-release-qualification/v02-release-candidate-artifact-build|operator-console-static/demo-data/v02-release-candidate-artifact-build\.json|scripts/v02-release-candidate-(check|evidence-check|local-run|no-go-regression|retention-check)\.(sh|py)$|services/brain-api/src/aion_brain/(contracts/v02_release_candidate\.py|v02_release_candidate/)|services/brain-api/tests/test_v02_release_candidate_artifact_build_aion243\.py$)'
}

if [[ "${AION_243_IMPLEMENTATION_CONTEXT:-0}" != "1" ]]; then
  if ! aion243_implementation_context; then
    ./scripts/v02-staging-qualification-operator-evaluation-no-go-regression.sh >/dev/null
  fi
fi

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
    "examples/v02-release-qualification/release-candidate-authorization.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    if payload.get("active_v02_release_qualification_authorization") != c.AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit(f"{relative} active authorization mismatch")
    if payload.get("authorization_active") is not True:
        raise SystemExit(f"{relative} authorization must remain active")
    if payload.get("authorization_consumed") is not False:
        raise SystemExit(f"{relative} authorization must remain unconsumed")
    if payload.get("v02_release_ready") is not False:
        raise SystemExit(f"{relative} must keep v02_release_ready=false")
    if payload.get("v02_tag_created") is not False:
        raise SystemExit(f"{relative} must keep v02_tag_created=false")
    if payload.get("v02_release_created") is not False:
        raise SystemExit(f"{relative} must keep v02_release_created=false")
    if payload.get("release_candidate_published") is not False:
        raise SystemExit(f"{relative} must keep release_candidate_published=false")
    if payload.get("production_deployment_enabled") is not False:
        raise SystemExit(f"{relative} must keep production_deployment_enabled=false")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "deterministic v0.2 release candidate artifact build authorization no-go PASS"
