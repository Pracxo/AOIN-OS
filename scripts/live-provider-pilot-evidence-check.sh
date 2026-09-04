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
import sys
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts.live_provider_pilot import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    PILOT_ID,
    SELECTED_MODEL_ID,
    LiveProviderEvidenceBundle,
    default_zero_counters,
    evidence_report_fingerprint,
)

path = ROOT / "examples/adaptive-intelligence/live-provider-pilot-evidence.json"
if not path.exists():
    state = json.loads(
        (ROOT / "examples/adaptive-intelligence/live-provider-pilot-implementation-state.json")
        .read_text(encoding="utf-8")
    )
    if state.get("live_execution_state") != "pending_OPENAI_API_KEY_in_runner_process":
        raise SystemExit("AION-248 evidence missing without pending key state")
    print("OpenAI live provider pilot evidence PASS (pending authorized runner execution)")
    raise SystemExit(0)

payload = json.loads(path.read_text(encoding="utf-8"))
evidence = LiveProviderEvidenceBundle.model_validate(payload)
if evidence.pilot_id != PILOT_ID:
    raise SystemExit("AION-248 pilot ID mismatch")
if evidence.authorization_id != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-248 evidence authorization mismatch")
if evidence.selected_model_id != SELECTED_MODEL_ID:
    raise SystemExit("AION-248 evidence selected model mismatch")
if evidence.report_fingerprint != evidence_report_fingerprint(evidence.model_dump(mode="json")):
    raise SystemExit("AION-248 evidence fingerprint mismatch")
if len(evidence.request_projection_fingerprints) != 6:
    raise SystemExit("AION-248 must contain six requests")
if evidence.counters.get("successful_live_responses") != 6:
    raise SystemExit("AION-248 must contain six successful responses")
if evidence.zero_counters != default_zero_counters():
    raise SystemExit("AION-248 zero counters mismatch")
if evidence.credential_value_retained or evidence.credential_fingerprint_created:
    raise SystemExit("AION-248 credential retention violation")

print("OpenAI live provider pilot evidence PASS")
PY
