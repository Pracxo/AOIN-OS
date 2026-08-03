#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate
  local merge_base
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        if [[ -n "$merge_base" ]]; then
          echo "$merge_base"
          return 0
        fi
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      if [[ -n "$merge_base" ]]; then
        echo "$merge_base"
        return 0
      fi
    fi
  done
  if git_ref_exists HEAD~1; then
    echo HEAD~1
  fi
}

BASE="$(comparison_base || true)"
if [[ -n "$BASE" ]]; then
  CHANGED="$(git diff --name-only "$BASE" HEAD --)"
else
  CHANGED=""
fi

if printf '%s\n' "$CHANGED" | rg -n '^(services/brain-api/src/aion_brain|packages/aion-sdk-python/src|\.github/workflows/|migrations/|alembic/)' >/dev/null 2>&1; then
  echo "AION-244 must not modify runtime source, workflows or migrations" >&2
  exit 1
fi

if printf '%s\n' "$CHANGED" | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|poetry\.lock|requirements.*\.txt)$' >/dev/null 2>&1; then
  echo "AION-244 must not add dependency/package files" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    for key in (
        "production_runtime_authorized",
        "production_deployment_enabled",
        "production_exposure",
        "registry_login_enabled",
        "registry_pull_enabled",
        "registry_push_enabled",
        "public_package_registry_upload_enabled",
        "production_credentials_enabled",
        "production_tokens_enabled",
        "production_database_enabled",
    ):
        if payload.get(key, False) is not False:
            raise SystemExit(f"{relative} no-go mismatch {key}: {payload.get(key)!r}")

stable_tags = subprocess.run(
    ["git", "tag", "--list", "aion-v0.2.0", "v0.2.0*"],
    cwd=root,
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
if stable_tags:
    raise SystemExit(f"stable v0.2 tag exists: {stable_tags}")
PY

echo "AION-244 final evaluation no-go PASS"
