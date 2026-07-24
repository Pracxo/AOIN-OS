#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh

echo "knowledge intelligence claim graph no-go PASS"
