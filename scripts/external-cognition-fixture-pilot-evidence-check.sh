#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts.external_cognition import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    PROGRAM_ID,
    PROHIBITED_EFFECT_COUNTERS,
    external_cognition_fingerprint,
)

PATH = ROOT / "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json"
EXPECTED_COUNTERS = {
    "provider_manifests_loaded": 3,
    "model_manifests_loaded": 6,
    "model_capability_records_loaded": 18,
    "routing_policies_loaded": 6,
    "structured_output_schemas_loaded": 2,
    "fixture_sessions_started": 1,
    "fixture_sessions_closed": 1,
    "active_fixture_sessions_after_close": 0,
    "fixture_requests_submitted": 16,
    "route_plans_created": 9,
    "fixture_provider_invocations": 11,
    "fixture_responses_generated": 9,
    "successful_response_projections": 8,
    "structured_output_validations": 2,
    "structured_output_validation_failures": 1,
    "capability_rejections": 1,
    "context_budget_rejections": 1,
    "output_budget_rejections": 1,
    "cost_budget_rejections": 1,
    "latency_budget_rejections": 1,
    "normalized_provider_errors": 2,
    "retry_plans_created": 1,
    "fallback_plans_created": 1,
    "fallback_responses_generated": 1,
    "circuit_breaker_open_events": 1,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "operator_review_items_created": 8,
    "trust_assessments_created": 9,
    "uncertainty_projections_created": 9,
    "observability_snapshots_created": 1,
    "integrity_reports_created": 1,
    "temporary_files_retained": 0,
}

if not PATH.is_file():
    raise SystemExit("missing AION-246 deterministic fixture pilot evidence")
payload = json.loads(PATH.read_text(encoding="utf-8"))
expected_fingerprint = external_cognition_fingerprint(
    {key: value for key, value in payload.items() if key != "report_fingerprint"}
)
if payload.get("report_fingerprint") != expected_fingerprint:
    raise SystemExit("AION-246 evidence report fingerprint mismatch")
if payload.get("pilot_id") != "AION-246-deterministic-external-cognition-fixture-pilot":
    raise SystemExit("AION-246 pilot ID mismatch")
if payload.get("program_id") != PROGRAM_ID:
    raise SystemExit("AION-246 program ID mismatch")
if payload.get("authorization_id") != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-246 authorization ID mismatch")
if not re.fullmatch(r"[0-9a-f]{40}", str(payload.get("implementation_commit", ""))):
    raise SystemExit("AION-246 implementation commit must be a lowercase 40-character SHA")
if payload.get("counters") != EXPECTED_COUNTERS:
    raise SystemExit("AION-246 evidence counters mismatch")
if payload.get("prohibited_effect_counters") != PROHIBITED_EFFECT_COUNTERS:
    raise SystemExit("AION-246 prohibited effect counters mismatch")
for key in (
    "integrity_passed",
    "redacted",
):
    if payload.get(key) is not True:
        raise SystemExit(f"AION-246 evidence boolean must be true: {key}")
for key in (
    "provider_effect",
    "network_effect",
    "memory_effect",
    "tool_effect",
    "production_effect",
):
    if payload.get(key) is not False:
        raise SystemExit(f"AION-246 evidence effect flag must be false: {key}")
for top_level_key, value in EXPECTED_COUNTERS.items():
    if payload.get(top_level_key) != value:
        raise SystemExit(f"AION-246 evidence top-level counter mismatch: {top_level_key}")
serialized = json.dumps(payload, sort_keys=True).lower()
for marker in (
    "bearer ",
    "sk-",
    "api key",
    "authorization header value",
    "chain-of-thought",
    "hidden reasoning",
    "private key",
    "raw prompt value",
    "raw response value",
    "fixture-general-result",
    "temporary-root",
    "/private/tmp",
):
    if marker in serialized:
        raise SystemExit(f"AION-246 evidence contains prohibited retained material marker: {marker}")

print("external cognition deterministic fixture pilot evidence PASS")
PY
