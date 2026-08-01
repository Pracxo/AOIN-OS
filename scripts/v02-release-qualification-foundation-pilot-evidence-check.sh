#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c

path = Path(
    "examples/v02-release-qualification/"
    "v02-production-readiness-qualification-foundation-pilot-evidence.json"
)
payload = json.loads(path.read_text(encoding="utf-8"))
expected = c.v02_qualification_fingerprint(
    {key: value for key, value in payload.items() if key != "report_fingerprint"}
)
if payload.get("report_fingerprint") != expected:
    raise SystemExit("pilot evidence report_fingerprint mismatch")
required = {
    "pilot_id": c.PILOT_ID,
    "authorization_id": c.AUTHORIZATION_TRANSACTION_ID,
    "program_id": c.PROGRAM_ID,
    "mode": "deterministic-local-simulation",
    "qualification_decision": c.FOUNDATION_DECISION,
    "readiness_domains_evaluated": 20,
    "readiness_gaps_evaluated": 20,
    "identity_provider_manifests_validated": 1,
    "public_key_lifecycle_policies_validated": 3,
    "credential_lifecycle_policies_validated": 4,
    "token_lifecycle_policies_validated": 4,
    "session_lifecycle_policies_validated": 3,
    "replay_provisioning_plans_validated": 1,
    "deployment_artifact_manifests_validated": 1,
    "reproducibility_projections_validated": 2,
    "rollback_plans_validated": 2,
    "rollback_drill_plans_validated": 1,
    "rollback_drill_simulations": 1,
    "release_gates_evaluated": 24,
    "staging_qualification_plans_validated": 1,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "release_ready_decisions": 0,
    "release_hold_decisions": 1,
    "temporary_files_retained": 0,
    "temporary_paths_retained": 0,
}
for key, value in required.items():
    if payload.get(key) != value:
        raise SystemExit(f"pilot evidence mismatch {key}: {payload.get(key)!r}")
minimums = {
    "protected_material_classes_validated": 10,
    "sbom_components_projected": 12,
    "artifact_provenance_records_validated": 4,
    "observability_signals_validated": 24,
    "health_readiness_checks_validated": 12,
    "threat_scenarios_validated": 40,
}
for key, minimum in minimums.items():
    if payload.get(key, 0) < minimum:
        raise SystemExit(f"pilot evidence below minimum {key}")
for key in (
    "staging_evidence_required",
    "production_evidence_required",
    "integrity_passed",
    "redacted",
):
    if payload.get(key) is not True:
        raise SystemExit(f"pilot evidence must keep {key}=true")
for key in ("v02_release_ready", "v02_release_candidate_created", "production_effect", "runtime_effect"):
    if payload.get(key) is not False:
        raise SystemExit(f"pilot evidence must keep {key}=false")
if payload.get("prohibited_effect_counters") != c.PROHIBITED_EFFECT_COUNTERS:
    raise SystemExit("pilot evidence nested prohibited counters mismatch")
for key, value in c.PROHIBITED_EFFECT_COUNTERS.items():
    if payload.get(key) != value:
        raise SystemExit(f"pilot evidence prohibited counter mismatch {key}")
PY

echo "v0.2 release qualification foundation pilot evidence PASS"
