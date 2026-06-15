#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

run_ruff() {
  local project_dir="$1"
  cd "$ROOT_DIR/$project_dir"
  if [[ -x .venv/bin/ruff ]]; then
    .venv/bin/ruff check .
  else
    "${PYTHON:-python3}" -m ruff check .
  fi
}

run_ruff services/brain-api
run_ruff packages/aion-sdk-python
