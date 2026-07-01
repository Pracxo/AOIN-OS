#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export AION_CHECK_RUNNING="${AION_CHECK_RUNNING:-1}"

"$ROOT_DIR/scripts/verify-no-domain-drift.sh"
"$ROOT_DIR/scripts/lint.sh"
"$ROOT_DIR/scripts/test-brain.sh"
"$ROOT_DIR/scripts/test-sdk.sh"
"$ROOT_DIR/scripts/typecheck.sh"
"$ROOT_DIR/scripts/boundary-check.sh"
"$ROOT_DIR/scripts/repo-health.sh"
