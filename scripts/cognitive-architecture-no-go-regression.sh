#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode no-go

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if git diff --name-only origin/main...HEAD -- .github/workflows services/brain-api/src/aion_brain services/brain-api/pyproject.toml packages/aion-sdk-python/src migrations package.json package-lock.json pnpm-lock.yaml yarn.lock poetry.lock uv.lock requirements.txt 2>/dev/null | grep -q .; then
  echo "AION-183 must not change runtime source, workflows, migrations, or package manifests" >&2
  exit 1
fi

echo "cognitive architecture no-go PASS"
