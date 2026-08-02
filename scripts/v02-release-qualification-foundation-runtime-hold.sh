#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"

is_nested_gate_context() {
  [ -n "${PYTEST_CURRENT_TEST:-}" ] && return 0
  [ "${AION_V02_RELEASE_QUALIFICATION_FOUNDATION_SKIP_FULL_CHECK:-}" = "1" ] && return 0
  [ "${AION_AGGREGATE_GATE_RUNNING:-}" = "1" ] && return 0
  [ "${AION_CHECK_RUNNING:-}" = "1" ] && return 0
  return 1
}

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c
import v02_release_qualification_foundation_operator_evaluation as aion240
import v02_staging_qualification_operator_evaluation as aion242

aion243_evidence_exists = Path(
    "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
).is_file()

for label, path in (
    ("program", Path("docs/v02-release-qualification/program-ledger.json")),
    ("authorization", Path("docs/v02-release-qualification/authorization-ledger.json")),
):
    payload = json.loads(path.read_text(encoding="utf-8"))
    required_true = (
        "v02_release_qualification_foundation_implemented",
        "disabled_local_qualification_simulator_available",
        "local_qualification_pilot_completed",
    )
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{label} runtime hold requires {key}=true")
    post_closeout = (
        payload.get("active_v02_release_qualification_authorization")
        == aion240.NEXT_AUTHORIZATION_ID
    )
    post_aion242 = (
        payload.get("active_v02_release_qualification_authorization")
        == aion242.NEXT_AUTHORIZATION_ID
    )
    required_false = [
        "production_auth_runtime_enabled",
        "external_identity_provider_call_enabled",
        "credential_generation_enabled",
        "credential_read_enabled",
        "credential_persistence_enabled",
        "token_generation_enabled",
        "token_read_enabled",
        "token_persistence_enabled",
        "live_replay_ledger_enabled",
        "production_database_provisioning_enabled",
        "staging_deployment_enabled",
        "production_deployment_enabled",
        "rollback_execution_enabled",
        "production_observability_export_enabled",
        "external_log_export_enabled",
        "external_metric_export_enabled",
        "external_trace_export_enabled",
        "v02_release_candidate_created",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ]
    if post_closeout or post_aion242:
        expected_true = {
            "staging_runtime_authorized": True,
            "controlled_staging_qualification_authorized": True,
        }
        for key, expected in expected_true.items():
            if payload.get(key) is not expected:
                raise SystemExit(f"{label} runtime hold mismatch {key}: {payload.get(key)!r}")
        if payload.get("controlled_staging_qualification_implemented") is True:
            expected_state = "implemented_isolated_local_pilot_complete_pending_AION-242_closeout"
            if payload.get("controlled_staging_qualification_state") != expected_state:
                raise SystemExit(f"{label} controlled staging implementation state mismatch")
            if payload.get("local_staging_pilot_completed") is not True:
                raise SystemExit(f"{label} local staging pilot completion missing")
            if payload.get("active_staging_resources") != 0:
                raise SystemExit(f"{label} active staging resources must be zero")
        elif payload.get("controlled_staging_qualification_implemented") is not False:
            raise SystemExit(f"{label} controlled staging implementation flag mismatch")
        expected_task = (
            aion242.NEXT_IMPLEMENTATION_TASK
            if post_aion242
            else aion240.NEXT_IMPLEMENTATION_TASK
        )
        expected_closeout = (
            aion242.NEXT_FORMAL_CLOSEOUT_TASK
            if post_aion242
            else aion240.NEXT_FORMAL_CLOSEOUT_TASK
        )
        if payload.get("active_v02_release_qualification_task") != expected_task:
            raise SystemExit(f"{label} active task mismatch")
        if payload.get("formal_closeout_task") != expected_closeout:
            raise SystemExit(f"{label} closeout task mismatch")
        if post_aion242:
            if payload.get("controlled_staging_qualification_operator_evaluation_passed") is not True:
                raise SystemExit(f"{label} AION-242 operator evaluation pass missing")
            if payload.get("release_candidate_artifact_build_authorized") is not True:
                raise SystemExit(f"{label} release-candidate build authorization missing")
            if aion243_evidence_exists:
                if payload.get("release_candidate_artifact_build_implemented") is not True:
                    raise SystemExit(f"{label} AION-243 local release-candidate build state missing")
                if payload.get("release_candidate_created") is not True:
                    raise SystemExit(f"{label} AION-243 local release candidate state missing")
            else:
                if payload.get("release_candidate_artifact_build_implemented") is not False:
                    raise SystemExit(f"{label} release-candidate build must remain unimplemented")
                if payload.get("release_candidate_created") is not False:
                    raise SystemExit(f"{label} release candidate must remain absent")
            if payload.get("release_candidate_published") is not False:
                raise SystemExit(f"{label} release candidate must remain unpublished")
            closed = payload.get("aion_240_authorization_closeout", {})
            if closed.get("authorization_active") is not False:
                raise SystemExit(f"{label} AION-240 closeout active flag mismatch")
            if closed.get("authorization_consumed") is not True:
                raise SystemExit(f"{label} AION-240 closeout consumed flag mismatch")
        else:
            closed = payload.get("aion_238_authorization_closeout", {})
            if closed.get("authorization_active") is not False:
                raise SystemExit(f"{label} AION-238 closeout active flag mismatch")
            if closed.get("authorization_consumed") is not True:
                raise SystemExit(f"{label} AION-238 closeout consumed flag mismatch")
    else:
        required_false.append("staging_runtime_authorized")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{label} runtime hold mismatch {key}: {payload.get(key)!r}")
    expected_authorization = (
        aion242.NEXT_AUTHORIZATION_ID
        if post_aion242
        else aion240.NEXT_AUTHORIZATION_ID
        if post_closeout
        else c.AUTHORIZATION_TRANSACTION_ID
    )
    if payload.get("active_v02_release_qualification_authorization") != expected_authorization:
        raise SystemExit(f"{label} active authorization mismatch")
    if payload.get("authorization_active") is not True:
        raise SystemExit(f"{label} authorization must remain active")
    if payload.get("authorization_consumed") is not False:
        raise SystemExit(f"{label} authorization must remain unconsumed")
    if (
        not post_closeout
        and not post_aion242
        and payload.get("formal_closeout_task") != c.FORMAL_CLOSEOUT_TASK
    ):
        raise SystemExit(f"{label} closeout task mismatch")
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

echo "v0.2 release qualification foundation runtime hold PASS"
