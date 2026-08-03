#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode no-go

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -v '^aion-v0\.2\.0-rc\.1$' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if git diff --name-only origin/main...HEAD -- .github/workflows services/brain-api/pyproject.toml packages/aion-sdk-python/pyproject.toml package.json package-lock.json pnpm-lock.yaml yarn.lock poetry.lock uv.lock requirements.txt 2>/dev/null | while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  if aion243_is_scoped_v02_release_candidate_artifact_build_path "$path"; then
    continue
  fi
  printf '%s\n' "$path"
done | grep -q .; then
  echo "self-improvement authorization must not change workflows or package manifests" >&2
  exit 1
fi

echo "self-improvement governance no-go PASS"
