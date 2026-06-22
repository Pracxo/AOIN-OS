#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

run_format() {
  local project_dir="$1"
  cd "$ROOT_DIR/$project_dir"
  if [[ -x .venv/bin/ruff ]]; then
    .venv/bin/ruff format .
  else
    "${PYTHON:-python3}" -m ruff format .
  fi
}

run_format services/brain-api
run_format packages/aion-sdk-python
