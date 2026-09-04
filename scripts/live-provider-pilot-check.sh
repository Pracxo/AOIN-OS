#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/live-provider-pilot-no-go-regression.sh

if [[ -n "${PYTEST_CURRENT_TEST:-}" ]] || [[ "${AION_LIVE_PROVIDER_PILOT_SKIP_PYTEST:-}" == "1" ]]; then
  echo "PASS: focused AION-248 pytest deferred to outer test context"
else
  "$PYTHON_BIN" -m pytest services/brain-api/tests/test_live_provider_pilot_aion248.py -q
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts.live_provider_pilot import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    ENDPOINT_HOST,
    ENDPOINT_PATH,
    ENDPOINT_SCHEME,
    HTTP_METHOD,
    PILOT_CONFIRMATION_TEXT,
    SELECTED_MODEL_ID,
    LiveProviderAuthorizationEnvelope,
)

required_docs = {
    "docs/adaptive-intelligence/live-provider-pilot-implementation.md",
    "docs/adaptive-intelligence/live-provider-pilot-contracts.md",
    "docs/adaptive-intelligence/openai-responses-api-boundary.md",
    "docs/adaptive-intelligence/live-provider-operator-runbook.md",
    "docs/release/v03-live-provider-pilot.md",
    "docs/adr/0212-single-openai-responses-api-synthetic-live-provider-pilot.md",
}
required_examples = {
    "examples/adaptive-intelligence/live-provider-pilot-authorization.json",
    "examples/adaptive-intelligence/live-provider-pilot-contract-examples.json",
    "examples/adaptive-intelligence/live-provider-pilot-implementation-state.json",
    "operator-console-static/demo-data/live-provider-pilot-provider-selection.json",
    "operator-console-static/demo-data/live-provider-pilot-runtime-hold.json",
}
for path in sorted(required_docs | required_examples):
    if not (ROOT / path).is_file():
        raise SystemExit(f"required AION-248 artifact missing: {path}")

authorization = LiveProviderAuthorizationEnvelope()
if authorization.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-248 authorization mismatch")
if authorization.selected_model_id != SELECTED_MODEL_ID:
    raise SystemExit("AION-248 selected model mismatch")
if (
    authorization.endpoint_scheme,
    authorization.endpoint_host,
    authorization.endpoint_path,
    authorization.http_method,
) != (ENDPOINT_SCHEME, ENDPOINT_HOST, ENDPOINT_PATH, HTTP_METHOD):
    raise SystemExit("AION-248 endpoint mismatch")

runner = ROOT / "scripts/live-provider-pilot-local-run.py"
if stat.S_IMODE(runner.stat().st_mode) & stat.S_IXUSR == 0:
    raise SystemExit("AION-248 runner is not executable")
runner_text = runner.read_text(encoding="utf-8")
contract_text = (
    ROOT / "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py"
).read_text(encoding="utf-8")
if PILOT_CONFIRMATION_TEXT not in runner_text and PILOT_CONFIRMATION_TEXT not in contract_text:
    raise SystemExit("AION-248 runner confirmation text missing")

ledger = json.loads((ROOT / "docs/adaptive-intelligence/program-ledger.json").read_text())
if ledger.get("active_adaptive_intelligence_authorization") != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-248 active authorization mismatch")
if ledger.get("active_adaptive_intelligence_authorization_count") != 1:
    raise SystemExit("AION-248 requires exactly one active Adaptive Intelligence authorization")
record = ledger.get("aion_247_record", {})
if record.get("pull_requests") != [167] or record.get("ci_result") != "pass":
    raise SystemExit("AION-247 delivery reconciliation is incomplete")
aion248 = ledger.get("aion_248_record", {})
if aion248.get("runtime_state") != (
    "single_openai_responses_api_live_provider_pilot_implementation_ready_live_execution_pending"
):
    raise SystemExit("AION-248 implementation-ready record mismatch")

print("single OpenAI Responses API synthetic live provider pilot PASS")
PY
