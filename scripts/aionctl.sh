#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../packages/aion-sdk-python"
PYTHON_BIN="${PYTHON:-python3}"
"$PYTHON_BIN" -m aion_sdk.cli.main "$@"
