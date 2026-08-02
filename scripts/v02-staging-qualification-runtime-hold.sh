#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

is_nested_gate_context() {
  [ -n "${PYTEST_CURRENT_TEST:-}" ] && return 0
  [ "${AION_V02_STAGING_QUALIFICATION_SKIP_FULL_CHECK:-}" = "1" ] && return 0
  [ "${AION_AGGREGATE_GATE_RUNNING:-}" = "1" ] && return 0
  [ "${AION_CHECK_RUNNING:-}" = "1" ] && return 0
  return 1
}

./scripts/v02-staging-qualification-no-go-regression.sh >/dev/null
./scripts/v02-staging-qualification-pilot-evidence-check.sh >/dev/null

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_staging_qualification as c

runtime_hold = json.loads(
    Path("examples/v02-release-qualification/staging-runtime-hold.json").read_text(
        encoding="utf-8"
    )
)
program = json.loads(Path("docs/v02-release-qualification/program-ledger.json").read_text(encoding="utf-8"))
authorization = json.loads(Path("docs/v02-release-qualification/authorization-ledger.json").read_text(encoding="utf-8"))
evidence = json.loads(
    Path(
        "examples/v02-release-qualification/"
        "v02-controlled-isolated-staging-pilot-evidence.json"
    ).read_text(encoding="utf-8")
)
required_true = (
    "staging_qualification_authorized",
    "staging_qualification_implemented",
    "local_staging_pilot_completed",
)
for key in required_true:
    if runtime_hold.get(key) is not True:
        raise SystemExit(f"staging runtime hold requires {key}=true")
for key in (
    "active_qualification_sessions_after_close",
    "active_containers_after_cleanup",
    "active_volumes_after_cleanup",
    "active_networks_after_cleanup",
    "run_owned_images_after_cleanup",
):
    if runtime_hold.get(key) != 0 or evidence.get(key) != 0:
        raise SystemExit(f"staging runtime hold counter must be zero: {key}")
for key in (
    "registry_login_enabled",
    "registry_pull_enabled",
    "registry_push_enabled",
    "public_network_access_enabled",
    "dns_resolution_enabled",
    "external_identity_provider_call_enabled",
    "production_identity_provider_enabled",
    "production_credential_generation_enabled",
    "production_token_generation_enabled",
    "production_database_operation_enabled",
    "production_deployment_enabled",
    "release_candidate_creation_enabled",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
):
    if runtime_hold.get(key) is not False:
        raise SystemExit(f"staging runtime hold mismatch {key}: {runtime_hold.get(key)!r}")
for label, payload in (("program", program), ("authorization", authorization)):
    if payload.get("active_v02_release_qualification_authorization") != c.AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit(f"{label} active authorization mismatch")
    if payload.get("active_v02_release_qualification_authorization_count") != 1:
        raise SystemExit(f"{label} active authorization count mismatch")
    if payload.get("active_v02_release_qualification_task") != c.IMPLEMENTATION_TASK:
        raise SystemExit(f"{label} active task mismatch")
    if payload.get("formal_closeout_task") != c.FORMAL_CLOSEOUT_TASK:
        raise SystemExit(f"{label} formal closeout mismatch")
    if payload.get("authorization_active") is not True:
        raise SystemExit(f"{label} authorization must remain active")
    if payload.get("authorization_consumed") is not False:
        raise SystemExit(f"{label} authorization must remain unconsumed")
    if payload.get("authorization_expired") is not False:
        raise SystemExit(f"{label} authorization must not be expired")
    if payload.get("authorization_reusable") is not False:
        raise SystemExit(f"{label} authorization must remain non-reusable")
    if payload.get("controlled_staging_qualification_implemented") is not True:
        raise SystemExit(f"{label} controlled staging implementation missing")
    if payload.get("local_staging_pilot_completed") is not True:
        raise SystemExit(f"{label} local pilot completion missing")
    if payload.get("active_staging_resources") != 0:
        raise SystemExit(f"{label} active staging resources must be zero")
    for key in (
        "production_runtime_authorized",
        "production_deployment_enabled",
        "release_candidate_creation_enabled",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"{label} runtime hold mismatch {key}: {payload.get(key)!r}")
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

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 env -u AION_BRAIN_PYTHON ./scripts/check.sh
fi

echo "controlled isolated staging qualification runtime hold PASS"
