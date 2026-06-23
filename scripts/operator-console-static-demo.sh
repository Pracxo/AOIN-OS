#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

offline_ok=false
skip_api=false
serve=false
api_url="http://localhost:8080"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline-ok)
      offline_ok=true
      shift
      ;;
    --skip-api)
      skip_api=true
      shift
      ;;
    --serve)
      serve=true
      shift
      ;;
    --api-url)
      api_url="${2:-}"
      if [[ -z "$api_url" ]]; then
        echo "--api-url requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

./scripts/operator-console-static-check.sh

echo "Static console command:"
echo "python3 -m http.server 8090 --directory operator-console-static"
echo "Open: http://localhost:8090?api=$api_url"

if [[ "$serve" == true ]]; then
  exec python3 -m http.server 8090 --directory operator-console-static
fi

if [[ "$skip_api" == true ]]; then
  echo "API checks skipped; offline demo data remains available."
  echo "Operator console static demo PASS"
  exit 0
fi

python3 - "$api_url" <<'PY'
from __future__ import annotations

import sys
from urllib.parse import urlparse

parsed = urlparse(sys.argv[1])
if parsed.hostname not in {"localhost", "127.0.0.1"}:
    raise SystemExit("API URL must be localhost or 127.0.0.1")
if parsed.scheme not in {"http", "https"}:
    raise SystemExit("API URL must use http or https")
PY

if ! command -v curl >/dev/null 2>&1; then
  if [[ "$offline_ok" == true ]]; then
    echo "curl unavailable; offline demo mode accepted."
    echo "Operator console static demo PASS"
    exit 0
  fi
  echo "curl unavailable and offline mode not allowed" >&2
  exit 1
fi

if ! curl --fail --silent --show-error --max-time 2 "$api_url/health" >/tmp/aion-operator-console-health.json; then
  if [[ "$offline_ok" == true ]]; then
    echo "Local API unavailable; offline demo mode accepted."
    echo "Operator console static demo PASS"
    exit 0
  fi
  echo "Local API unavailable and offline mode not allowed" >&2
  exit 1
fi

view_payload='{"view":"overview","owner_scope":["workspace:main"],"include_actions":true,"include_forbidden_actions":true,"include_refs":true,"metadata":{"static_prototype":true}}'
if ! curl --fail --silent --show-error --max-time 2 \
  -H "Content-Type: application/json" \
  -d "$view_payload" \
  "$api_url/brain/operator-console/view-model" >/tmp/aion-operator-console-view-model.json; then
  if [[ "$offline_ok" == true ]]; then
    echo "View-model API unavailable; offline demo mode accepted."
    echo "Operator console static demo PASS"
    exit 0
  fi
  echo "View-model API unavailable and offline mode not allowed" >&2
  exit 1
fi

echo "Operator console static demo PASS"
