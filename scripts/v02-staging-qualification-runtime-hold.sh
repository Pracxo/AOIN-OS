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

./scripts/v02-staging-qualification-authorization-check.sh >/dev/null

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

runtime_hold = json.loads(
    Path("examples/v02-release-qualification/staging-runtime-hold.json").read_text(
        encoding="utf-8"
    )
)
required_false = (
    "staging_qualification_implemented",
    "registry_login_enabled",
    "registry_pull_enabled",
    "registry_push_enabled",
    "public_network_access_enabled",
    "dns_resolution_enabled",
    "production_runtime_authorized",
    "release_candidate_creation_enabled",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)
for key in required_false:
    if runtime_hold.get(key) is not False:
        raise SystemExit(f"staging runtime hold mismatch {key}: {runtime_hold.get(key)!r}")
for key in ("actual_builds_executed", "staging_deployments", "rollback_executions"):
    if runtime_hold.get(key) != 0:
        raise SystemExit(f"staging runtime hold counter must be zero: {key}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 env -u AION_BRAIN_PYTHON ./scripts/check.sh
fi

echo "controlled isolated staging qualification runtime hold PASS"
