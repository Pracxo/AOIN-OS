#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${AION_BRAIN_API_URL:-http://localhost:8080}"
OFFLINE_OK=false
SKIP_API=false

for arg in "$@"; do
  case "$arg" in
    --offline-ok)
      OFFLINE_OK=true
      ;;
    --skip-api)
      SKIP_API=true
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
example_dir = root / "examples" / "model-providers"
required = [
    "generic-provider-profile.json",
    "prompt-egress-preview-request.json",
    "provider-simulation-request.json",
    "provider-readiness-request.json",
]
for name in required:
    path = example_dir / name
    if not path.exists():
        raise SystemExit(f"missing example: {path}")
    payload = json.loads(path.read_text())
    text = json.dumps(payload, sort_keys=True).lower()
    forbidden = ("api_key", "apikey", "authorization", "bearer ", "secret", "sk-", "http://", "https://")
    if any(item in text for item in forbidden):
        raise SystemExit(f"unsafe provider example content: {path}")
    if "raw prompt" in text or "hidden reasoning" in text:
        raise SystemExit(f"unsafe prompt content marker: {path}")

profile = json.loads((example_dir / "generic-provider-profile.json").read_text())
if profile.get("external_calls_allowed") is not False:
    raise SystemExit("profile external_calls_allowed must be false")
if profile.get("credentials_required") is not False:
    raise SystemExit("profile credentials_required must be false")
if profile.get("supported_modes") != ["dry_run"]:
    raise SystemExit("profile supported_modes must be ['dry_run']")

preview = json.loads((example_dir / "prompt-egress-preview-request.json").read_text())
summary = preview.get("prompt_summary") or {}
if summary.get("raw_prompt_included") is not False:
    raise SystemExit("egress preview must not include prompt body")
if summary.get("hidden_reasoning_included") is not False:
    raise SystemExit("egress preview must not include hidden reasoning")

simulation = json.loads((example_dir / "provider-simulation-request.json").read_text())
if simulation.get("simulation_type") != "dry_run":
    raise SystemExit("simulation must be dry_run")
if simulation.get("metadata", {}).get("external_calls_made") is not False:
    raise SystemExit("simulation external calls must be false")
if simulation.get("metadata", {}).get("model_invoked") is not False:
    raise SystemExit("simulation model invocation must be false")

readiness = json.loads((example_dir / "provider-readiness-request.json").read_text())
metadata = readiness.get("metadata") or {}
if metadata.get("expected_external_call_ready") is not False:
    raise SystemExit("readiness must expect external_call_ready false")
if metadata.get("expected_credentials_ready") is not False:
    raise SystemExit("readiness must expect credentials_ready false")

print("Model provider examples PASS")
PY

if [[ "$SKIP_API" == "true" ]]; then
  echo "Model provider API checks skipped"
  echo "Model provider check PASS"
  exit 0
fi

if ! curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  if [[ "$OFFLINE_OK" == "true" ]]; then
    echo "WARN: AION API unavailable; offline mode accepted"
    echo "Model provider check PASS"
    exit 0
  fi
  echo "AION API unavailable; use --offline-ok or --skip-api for local-only checks" >&2
  exit 1
fi

curl -fsS -X POST "$BASE_URL/brain/model-providers/profiles/seed-defaults" \
  -H "content-type: application/json" \
  --data '{"scope":["workspace:main"],"dry_run":true}' >/dev/null

curl -fsS -X POST "$BASE_URL/brain/model-providers/readiness" \
  -H "content-type: application/json" \
  --data @"$ROOT_DIR/examples/model-providers/provider-readiness-request.json" >/dev/null

echo "Model provider check PASS"
