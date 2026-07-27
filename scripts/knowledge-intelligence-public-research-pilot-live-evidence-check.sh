#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.knowledge_public_research_pilot import (
    AUTHORIZATION_TRANSACTION_ID,
    PUBLIC_RESEARCH_RESOURCE_LIMITS,
    PublicResearchPilotMode,
    validate_hex64,
)

root = Path(os.environ["AION_REPO_ROOT"])
path = root / "examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json"
if not path.is_file():
    raise SystemExit("committed redacted live-evidence summary is missing")
payload = json.loads(path.read_text(encoding="utf-8"))

expected = {
    "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
    "mode": PublicResearchPilotMode.OPERATOR_INVOKED_LIVE.value,
    "external_read_performed": True,
    "operator_review_required": True,
    "source_bodies_retained": 0,
    "source_bodies_persisted": 0,
    "automatic_promotions": 0,
    "cognitive_memory_writes": 0,
    "belief_mutations": 0,
    "persistent_verified_knowledge_writes": 0,
    "background_execution": False,
    "production_exposure": False,
    "kill_switch_available": True,
    "budget_within_limits": True,
    "integrity_passed": True,
    "redacted": True,
}
for key, value in expected.items():
    if payload.get(key) != value:
        raise SystemExit(f"live evidence mismatch {key}: {payload.get(key)!r}")

for key in (
    "pilot_session_id",
    "source_candidate_count",
    "source_control_group_count",
    "public_https_request_count",
    "robots_request_count",
    "DNS_resolution_count",
    "redirect_count",
    "successful_source_count",
    "rejected_source_count",
    "source_snapshot_count",
    "source_provenance_count",
    "citation_count",
    "candidate_count",
    "candidate_eligibility_statuses",
    "report_fingerprint",
    "created_at",
):
    if key not in payload:
        raise SystemExit(f"live evidence missing field: {key}")

if payload["source_candidate_count"] < 3:
    raise SystemExit("live evidence must record at least three explicit source candidates")
if payload["source_control_group_count"] < 1:
    raise SystemExit("live evidence must record source control groups")
if not 1 <= payload["public_https_request_count"] <= PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_public_https_requests_per_plan"]:
    raise SystemExit("public HTTPS request count outside budget")
if not 1 <= payload["DNS_resolution_count"] <= PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_dns_resolutions_per_plan"]:
    raise SystemExit("DNS resolution count outside budget")
if payload["robots_request_count"] > PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_robots_fetches_per_plan"]:
    raise SystemExit("robots request count outside budget")
if payload["redirect_count"] > PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_redirects_per_fetch"] * payload["source_candidate_count"]:
    raise SystemExit("redirect count outside budget")
if payload["successful_source_count"] < 1:
    raise SystemExit("live pilot must have at least one successful HTTPS acquisition")
if payload["source_snapshot_count"] < 1 or payload["source_provenance_count"] < 1:
    raise SystemExit("live pilot evidence must include source lineage")
if payload["candidate_count"] < 1 or not payload["candidate_eligibility_statuses"]:
    raise SystemExit("live pilot evidence must include candidate status")

for key in (
    "dns_validation_passed",
    "peer_validation_passed",
    "tls_validation_passed",
    "pipeline_trace_present",
    "source_body_absent",
    "credentials_absent",
):
    if payload.get(key) is not True:
        raise SystemExit(f"live evidence required boolean is not true: {key}")

validate_hex64(str(payload["report_fingerprint"]), "live report fingerprint")
for key, value in payload.items():
    if key.lower() in {"body", "source_body", "content_bytes", "raw_body"}:
        raise SystemExit(f"source body field must not be committed: {key}")
    if isinstance(value, str):
        lowered = value.lower()
        if "authorization:" in lowered or "cookie:" in lowered or "bearer " in lowered:
            raise SystemExit("credential-bearing text found in live evidence")
PY

echo "knowledge intelligence public research pilot live evidence PASS"
