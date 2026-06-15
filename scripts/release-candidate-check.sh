#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if "$ROOT_DIR/scripts/check.sh" \
  && "$ROOT_DIR/scripts/docker-build.sh" \
  && "$ROOT_DIR/scripts/migration-check.sh" \
  && "$ROOT_DIR/scripts/verify-no-domain-drift.sh"; then
  echo "AION release candidate check PASS"
  echo "Next manual steps:"
  echo "- scripts/docker-up-core.sh"
  echo "- scripts/kernel-self-test.sh"
  echo "- scripts/export-contracts.sh"
  echo "- scripts/policy-coverage.sh"
else
  echo "AION release candidate check FAIL"
  exit 1
fi
