#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../packages/aion-sdk-python"
if [[ -x .venv/bin/pytest ]]; then
  .venv/bin/pytest "$@"
else
  "${PYTHON:-python3}" -m pytest "$@"
fi
