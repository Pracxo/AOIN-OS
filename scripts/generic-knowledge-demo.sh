#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PACK_DIR="$ROOT_DIR/examples/modules/generic-knowledge-intelligence"
API_URL="http://localhost:8080"
OFFLINE_OK=0
SKIP_API=0
KEEP_GOING=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline-ok) OFFLINE_OK=1; shift ;;
    --skip-api) SKIP_API=1; shift ;;
    --keep-going) KEEP_GOING=1; shift ;;
    --api-url)
      API_URL="${2:?--api-url requires a value}"
      shift 2
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

cd "$ROOT_DIR"

run_step() {
  local name="$1"
  shift
  echo
  echo "==> ${name}"
  if "$@"; then
    echo "PASS: ${name}"
    return 0
  fi
  echo "FAIL: ${name}" >&2
  if [[ "$KEEP_GOING" == "1" ]]; then
    return 0
  fi
  return 1
}

is_local_api_url() {
  case "$API_URL" in
    http://localhost:*|http://127.0.0.1:*|http://0.0.0.0:*) return 0 ;;
    *) return 1 ;;
  esac
}

api_reachable() {
  curl -fsS "${API_URL}/health" >/dev/null 2>&1
}

post_json() {
  local endpoint="$1"
  local file="$2"
  curl -fsS -X POST \
    -H 'content-type: application/json' \
    "${API_URL}${endpoint}" \
    --data-binary @"$file" >/dev/null
}

post_json_array() {
  local endpoint="$1"
  local file="$2"
  python3 - "$endpoint" "$file" "$API_URL" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

endpoint, file_name, api_url = sys.argv[1:4]
items = json.loads(Path(file_name).read_text())
if not isinstance(items, list):
    raise SystemExit("expected JSON array")
for item in items:
    subprocess.run(
        [
            "curl",
            "-fsS",
            "-X",
            "POST",
            "-H",
            "content-type: application/json",
            f"{api_url}{endpoint}",
            "--data-binary",
            "@-",
        ],
        input=json.dumps(item),
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
    )
PY
}

post_extracted_gate_request() {
  local tmp_file
  tmp_file="$(mktemp)"
  python3 - <<'PY' > "$tmp_file"
import json
from pathlib import Path

payload = json.loads(Path("examples/modules/generic-knowledge-intelligence/activation-gate-request.json").read_text())
print(json.dumps(payload["request"]))
PY
  curl -fsS -X POST \
    -H 'content-type: application/json' \
    "${API_URL}/brain/module-activation/requests/gki-activation-request-001/gate" \
    --data-binary @"$tmp_file" >/dev/null
  rm -f "$tmp_file"
}

echo "Generic Knowledge Intelligence metadata-only demo"
echo "API: ${API_URL}"

run_step "module pack check" ./scripts/module-pack-check.sh

if [[ "$SKIP_API" == "1" ]]; then
  echo
  echo "Skipping API checks because --skip-api is set."
  echo "Offline validation passed for Generic Knowledge Intelligence."
else
  if ! is_local_api_url; then
    echo "Refusing non-local API URL: ${API_URL}" >&2
    exit 2
  fi

  if api_reachable; then
    run_step "health" curl -fsS "${API_URL}/health"
    run_step "manifest validation" post_json \
      "/brain/extensions/manifests/validate" \
      "$PACK_DIR/manifest.json"
    run_step "extension intake dry-run" post_json \
      "/brain/extensions/intake" \
      "$PACK_DIR/intake-request.json"
    run_step "module slot dry-run metadata record" post_json \
      "/brain/module-slots" \
      "$PACK_DIR/module-slot-request.json"
    run_step "capability binding metadata records" post_json_array \
      "/brain/capability-bindings" \
      "$PACK_DIR/capability-bindings.json"
    run_step "binding validation dry-run" post_json \
      "/brain/module-bindings/validate" \
      "$PACK_DIR/binding-validation-request.json"
    run_step "module mock profile record" post_json \
      "/brain/module-mock/profiles" \
      "$PACK_DIR/mock-profile.json"
    run_step "module mock invocation dry-run" post_json \
      "/brain/module-mock/invoke" \
      "$PACK_DIR/mock-invocation-request.json"
    run_step "conformance dry-run" post_json \
      "/brain/conformance/run" \
      "$PACK_DIR/conformance-run-request.json"
    run_step "readiness assessment dry-run" post_json \
      "/brain/readiness/assess" \
      "$PACK_DIR/readiness-assessment-request.json"
    run_step "activation request dry-run" post_json \
      "/brain/module-activation/requests" \
      "$PACK_DIR/activation-request.json"
    run_step "activation gate dry-run" post_extracted_gate_request
  elif [[ "$OFFLINE_OK" == "1" ]]; then
    echo
    echo "Brain API is unavailable at ${API_URL}; offline validation passed."
  else
    echo "Brain API is unavailable at ${API_URL}." >&2
    exit 1
  fi
fi

echo
echo "Readiness trail summary:"
echo "  manifest: metadata-only"
echo "  capabilities: generic.knowledge.retrieve, summarize, ground, explain, answer"
echo "  mode: dry_run"
echo "  controlled_supported: false"
echo "  activation_ready: false"
echo "  activation_allowed: false"
echo "  runtime_registration_allowed: false"
echo "  module_mock_runtime: synthetic dry-run evidence only"
echo "  module_mock_execution_allowed: false"
echo "  expected blockers: activation_disabled, runtime_registration_disabled, code_loading_disabled"
echo
echo "Next evidence docs:"
echo "  docs/modules/generic-knowledge-intelligence-demo.md"
echo "  docs/modules/generic-knowledge-intelligence-readiness-trail.md"
echo "  docs/modules/generic-knowledge-intelligence-operator-review.md"
echo "  docs/modules/generic-knowledge-intelligence-mock-runtime.md"
