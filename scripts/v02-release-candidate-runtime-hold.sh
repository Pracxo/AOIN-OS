#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c

root = Path.cwd()
evidence_exists = (
    root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
).is_file()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
    "examples/v02-release-qualification/release-candidate-authorization.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    active_authorization = payload.get("active_v02_release_qualification_authorization")
    completed_rc1_prerelease = (
        active_authorization is None
        and payload.get("active_v02_release_qualification_authorization_count") == 0
        and payload.get("program_state") == "v02_release_qualification_program_complete_rc1_prerelease_published"
    )
    if payload.get("release_candidate_artifact_build_authorized") is not True:
        raise SystemExit(f"{relative} must authorize release-candidate build")
    if evidence_exists:
        if payload.get("release_candidate_artifact_build_implemented") is not True:
            raise SystemExit(f"{relative} must record local candidate implementation")
        if payload.get("release_candidate_created") is not True:
            raise SystemExit(f"{relative} must record local candidate creation")
        if payload.get("candidate_bundle_retained") is not True:
            raise SystemExit(f"{relative} must record candidate bundle retention")
    strict_false_keys = [
        "release_candidate_published",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ]
    if completed_rc1_prerelease:
        strict_false_keys = []
        if payload.get("release_candidate_published") is not True:
            raise SystemExit(f"{relative} RC1 prerelease publication must be recorded")
        if payload.get("v02_prerelease_created") is not True:
            raise SystemExit(f"{relative} RC1 prerelease creation must be recorded")
        if payload.get("v02_tag_created") is not True:
            raise SystemExit(f"{relative} RC1 tag creation must be recorded")
        if payload.get("v02_release_created") is not True:
            raise SystemExit(f"{relative} RC1 release creation must be recorded")
        if payload.get("v02_stable_release_created") is not False:
            raise SystemExit(f"{relative} stable v0.2 release must remain absent")
        if payload.get("formal_closeout_task") is not None:
            raise SystemExit(f"{relative} complete RC1 publication must not retain an active closeout task")
    for key in (
        *strict_false_keys,
        "release_candidate_promoted",
        "production_runtime_authorized",
        "production_deployment_enabled",
    ):
        if payload.get(key, False) is not False:
            raise SystemExit(f"{relative} runtime hold mismatch {key}: {payload.get(key)!r}")
    if active_authorization == c.AUTHORIZATION_TRANSACTION_ID:
        if payload.get("authorization_active") is not True:
            raise SystemExit(f"{relative} authorization must remain active")
        if payload.get("authorization_consumed") is not False:
            raise SystemExit(f"{relative} authorization must remain unconsumed")
    elif active_authorization == "AION-244-V02REL-0001":
        closeout = payload.get("aion_242_authorization_closeout", {})
        publication_auth = payload.get("aion_244_publication_authorization", {})
        if closeout.get("authorization_transaction_id") != c.AUTHORIZATION_TRANSACTION_ID:
            raise SystemExit(f"{relative} missing AION-242 closeout")
        if closeout.get("authorization_active") is not False or closeout.get("authorization_consumed") is not True:
            raise SystemExit(f"{relative} AION-242 closeout state mismatch")
        if publication_auth.get("authorization_active") is not True or publication_auth.get("authorization_consumed") is not False:
            raise SystemExit(f"{relative} AION-244 publication authorization state mismatch")
    elif completed_rc1_prerelease:
        pass
    else:
        raise SystemExit(f"{relative} active authorization mismatch")
    if active_authorization is not None and payload.get("formal_closeout_task") != c.FORMAL_CLOSEOUT_TASK:
        raise SystemExit(f"{relative} formal closeout must remain AION-244")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list | rg -n '^(v0\.2|v0\.2\.0|aion-v0\.2|aion-v0\.2\.0)$'; then
  echo "ERROR: stable v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 GitHub release exists" >&2
    exit 1
  fi
fi

echo "deterministic v0.2 release candidate runtime hold PASS"
