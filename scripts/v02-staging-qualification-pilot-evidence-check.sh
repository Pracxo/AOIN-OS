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
import re
from pathlib import Path

from aion_brain.contracts import v02_staging_qualification as c

path = Path(
    "examples/v02-release-qualification/"
    "v02-controlled-isolated-staging-pilot-evidence.json"
)
if not path.is_file():
    raise SystemExit("missing AION-241 committed pilot evidence")
payload = json.loads(path.read_text(encoding="utf-8"))
expected = c.v02_staging_fingerprint(
    {key: value for key, value in payload.items() if key != "report_fingerprint"}
)
if payload.get("report_fingerprint") != expected:
    raise SystemExit("pilot evidence report_fingerprint mismatch")
required = {
    "pilot_id": c.PILOT_ID,
    "authorization_id": c.AUTHORIZATION_TRANSACTION_ID,
    "program_id": c.PROGRAM_ID,
    "mode": "controlled-local-docker",
    "source_snapshot_commit": payload.get("implementation_commit"),
    "reproducibility_invariants_passed": True,
    "integrity_passed": True,
    "temporary_files_retained": 0,
    "redacted": True,
    "production_effect": False,
    "release_effect": False,
    "v02_release_ready": False,
    "v02_tag_created": False,
    "v02_release_created": False,
}
for key, value in required.items():
    if payload.get(key) != value:
        raise SystemExit(f"pilot evidence mismatch {key}: {payload.get(key)!r}")
for key in (
    "implementation_commit",
    "source_snapshot_commit",
):
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(payload.get(key, ""))):
        raise SystemExit(f"pilot evidence has invalid Git object: {key}")
for key in (
    "source_tree_fingerprint",
    "git_archive_fingerprint",
    "docker_context_fingerprint",
    "docker_server_fingerprint",
    "base_image_fingerprint",
    "build_plan_fingerprint",
    "generated_dockerfile_fingerprint",
    "build_context_fingerprint",
    "deployed_staging_image_fingerprint",
    "sbom_fingerprint",
    "artifact_provenance_chain_head",
    "reproducibility_comparison_fingerprint",
    "environment_profile_fingerprint",
    "compose_plan_fingerprint",
    "internal_network_fingerprint",
    "identity_fixture_fingerprint",
    "replay_fixture_fingerprint",
    "health_readiness_report_fingerprint",
    "security_validation_report_fingerprint",
    "observability_snapshot_fingerprint",
    "rollback_plan_fingerprint",
    "rollback_result_fingerprint",
    "cleanup_result_fingerprint",
):
    if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get(key, ""))):
        raise SystemExit(f"pilot evidence has invalid fingerprint: {key}")

minimums = {
    "artifact_provenance_records_created": 2,
    "health_checks_passed": 3,
    "readiness_checks_passed": 2,
    "security_tests_passed": 8,
    "replay_rejection_tests_passed": 1,
    "protected_material_redaction_tests_passed": 1,
    "configuration_drift_tests_passed": 1,
    "local_observability_records_created": 1,
    "loopback_listeners_created": 1,
}
for key, minimum in minimums.items():
    if payload.get(key, 0) < minimum:
        raise SystemExit(f"pilot evidence below minimum {key}: {payload.get(key)!r}")
exact = {
    **c.PILOT_COUNTERS,
    "staging_deployments_completed": 1,
    "isolated_networks_created": 1,
    "isolated_networks_removed": 1,
    "controlled_degradations_injected": 1,
    "health_failures_detected": 1,
    "staging_rollbacks_completed": 1,
    "post_rollback_health_recovered": True,
    "active_containers_after_cleanup": 0,
    "active_volumes_after_cleanup": 0,
    "active_networks_after_cleanup": 0,
    "run_owned_images_after_cleanup": 0,
}
for key, value in exact.items():
    if payload.get(key) != value:
        raise SystemExit(f"pilot evidence counter mismatch {key}: {payload.get(key)!r}")
for key, value in c.PROHIBITED_EFFECT_COUNTERS.items():
    if payload.get(key, payload.get("prohibited_effect_counters", {}).get(key)) != value:
        raise SystemExit(f"prohibited-effect counter mismatch: {key}")
if payload.get("prohibited_effect_counters") != c.PROHIBITED_EFFECT_COUNTERS:
    raise SystemExit("pilot evidence nested prohibited counters mismatch")
if payload.get("ephemeral_port_used") is not True:
    raise SystemExit("pilot evidence must record ephemeral_port_used=true")
if payload.get("actual_port_retained") is not False:
    raise SystemExit("pilot evidence must not retain actual port")
if payload.get("sbom_component_count", 0) < 1:
    raise SystemExit("pilot evidence SBOM component count mismatch")
if not payload.get("dependency_image_fingerprints"):
    raise SystemExit("pilot evidence dependency image fingerprints missing")
if not payload.get("staging_artifact_fingerprints"):
    raise SystemExit("pilot evidence staging artifact fingerprints missing")

serialized = json.dumps(payload, sort_keys=True).lower()
for marker in (
    "-----begin",
    "private key",
    "signed assertion",
    "database password",
    "postgres_password",
    "authorization: bearer",
    "sk-",
    "ghp_",
    "xoxb-",
    "temporary-root",
    "/tmp/aion241",
    "0.0.0.0",
):
    if marker in serialized:
        raise SystemExit(f"pilot evidence retained prohibited marker: {marker}")
PY

"$PYTHON_BIN" scripts/v02-staging-qualification-local-run.py audit-evidence >/dev/null

echo "controlled isolated staging qualification pilot evidence PASS"
