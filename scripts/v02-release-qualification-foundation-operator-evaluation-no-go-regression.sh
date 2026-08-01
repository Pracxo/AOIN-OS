#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
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
    echo "HEAD~1"
    return 0
  fi
  return 1
}

changed_paths() {
  local base
  base="$(comparison_base || true)"
  if [[ -n "$base" ]]; then
    git diff --name-only --diff-filter=ACMRT "$base" HEAD --
  fi
  git diff --name-only --diff-filter=ACMRT HEAD --
  git diff --cached --name-only --diff-filter=ACMRT --
  git ls-files --others --exclude-standard --
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/adr/0204-v02-qualification-foundation-evaluation-and-controlled-isolated-staging-qualification-authorization.md|\
    docs/adr/README.md|\
    docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/project-status.md|docs/visual-brain.md|\
    docs/v02-release-qualification/*|\
    docs/release/v02-qualification-foundation-operator-evaluation-*|\
    docs/release/v02-staging-qualification-*|\
    docs/release/v02-release-qualification-foundation-implementation.md|\
    docs/release/v02-release-qualification-foundation-pilot.md|\
    docs/release/v02-release-qualification-foundation-runtime-hold.md|\
    docs/release/v02-release-readiness-delta.md|\
    examples/v02-release-qualification/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/v02-qualification-foundation-operator-evaluation.json|\
    operator-console-static/demo-data/v02-staging-qualification-authorization.json|\
    operator-console-static/demo-data/v02-staging-environment-profile.json|\
    operator-console-static/demo-data/v02-staging-build-plan.json|\
    operator-console-static/demo-data/v02-staging-artifact-boundary.json|\
    operator-console-static/demo-data/v02-staging-rollback-boundary.json|\
    operator-console-static/demo-data/v02-staging-runtime-hold.json|\
    scripts/lib/v02_release_qualification_foundation_operator_evaluation.py|\
    scripts/v02-release-qualification-foundation-operator-evaluation-check.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-authorization-check.sh|\
    scripts/v02-staging-qualification-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-runtime-hold.sh|\
    services/brain-api/tests/test_v02_release_qualification_operator_evaluation_aion240.py)
      return 0
      ;;
  esac
  return 1
}

changed_paths | sort -u | while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if ! is_allowed_path "$path"; then
    echo "AION-240 changed path outside operator-evaluation boundary: $path" >&2
    exit 1
  fi
done

if changed_paths | sort -u | rg -n '^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-240 must not modify GitHub workflows" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|pyproject\.toml)$' >/dev/null 2>&1; then
  echo "AION-240 must not modify package manifests or lockfiles" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '(^migrations/|/migrations/)' >/dev/null 2>&1; then
  echo "AION-240 must not add migrations" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '^services/brain-api/src/aion_brain/' >/dev/null 2>&1; then
  echo "AION-240 primary branch must not modify runtime source" >&2
  exit 1
fi
if changed_paths | sort -u | rg -n '^packages/aion-sdk-python/src/' >/dev/null 2>&1; then
  echo "AION-240 primary branch must not modify SDK runtime source" >&2
  exit 1
fi

while IFS= read -r future_path; do
  [[ -z "$future_path" ]] && continue
  if [[ -e "$future_path" ]]; then
    echo "AION-240 must not create AION-241 source: $future_path" >&2
    exit 1
  fi
done <<'EOF'
services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py
services/brain-api/src/aion_brain/v02_staging_qualification
scripts/v02-staging-qualification-local-run.py
EOF

code_changes="$(
  changed_paths \
    | sort -u \
    | rg -n '^(scripts/.*(\.sh|\.py)|services/brain-api/tests/.*\.py)$' \
    | cut -d: -f2- \
    | rg -v 'no-go-regression\.sh$' \
    || true
)"
if [[ -n "$code_changes" ]]; then
  if rg -n '(^|[;&|[:space:]])docker([[:space:]]|$)|docker[._-]compose|subprocess\..*docker|os\.system\(|shell=True' $code_changes; then
    echo "AION-240 must not add Docker/build/deployment execution code" >&2
    exit 1
  fi
  if rg -n '(^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp)\b|urllib\.request|dns\.resolver|getaddrinfo\(|create_connection\()' $code_changes; then
    echo "AION-240 must not add network or DNS execution code" >&2
    exit 1
  fi
fi

secret_scan_paths="$(
  changed_paths \
    | sort -u \
    | rg -v '^(scripts/lib/v02_release_qualification_foundation_operator_evaluation\.py|scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression\.sh)$' \
    || true
)"
if [[ -n "$secret_scan_paths" ]]; then
  if rg -n 'sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|xoxb-|-----BEGIN PRIVATE KEY-----|client_secret[[:space:]]*=' $secret_scan_paths; then
    echo "AION-240 must not add credential or token material" >&2
    exit 1
  fi
fi

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    if payload.get("v02_release_ready") is not False:
        raise SystemExit(f"{relative} must keep v02_release_ready=false")
    if payload.get("v02_tag_created") is not False:
        raise SystemExit(f"{relative} must keep v02_tag_created=false")
    if payload.get("v02_release_created") is not False:
        raise SystemExit(f"{relative} must keep v02_release_created=false")
    if any(payload.get("prohibited_capabilities", {}).values()):
        raise SystemExit(f"{relative} has enabled prohibited capability")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "v0.2 release qualification foundation operator evaluation no-go PASS"
