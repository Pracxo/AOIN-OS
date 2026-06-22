#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT_DIR/scripts/test-brain.sh"
"$ROOT_DIR/scripts/test-sdk.sh"
