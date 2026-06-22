#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

run_mypy() {
  local project_dir="$1"
  cd "$ROOT_DIR/$project_dir"
  if [[ -x .venv/bin/mypy ]]; then
    .venv/bin/mypy src
  else
    "${PYTHON:-python3}" -m mypy src
  fi
}

run_mypy services/brain-api
run_mypy packages/aion-sdk-python
