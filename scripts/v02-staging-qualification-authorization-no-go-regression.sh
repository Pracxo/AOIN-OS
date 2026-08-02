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

./scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh >/dev/null

code_paths="$(
  changed_paths \
    | sort -u \
    | rg -n '^(scripts/.*(\.sh|\.py)|services/brain-api/tests/.*\.py)$' \
    | cut -d: -f2- \
    | rg -v '^scripts/v02-staging-qualification-local-run\.py$' \
    | rg -v '^scripts/lib/v02_staging_qualification_operator_evaluation\.py$' \
    | rg -v '^scripts/v02-staging-qualification-operator-evaluation-check\.sh$' \
    | rg -v '^scripts/v02-release-candidate-authorization-check\.sh$' \
    | rg -v '^scripts/v02-release-candidate-runtime-hold\.sh$' \
    | rg -v '^services/brain-api/tests/test_v02_staging_qualification_aion241\.py$' \
    | rg -v '^services/brain-api/tests/test_v02_staging_qualification_operator_evaluation_aion242\.py$' \
    | rg -v 'no-go-regression\.sh$' \
    || true
)"
if [[ -n "$code_paths" ]]; then
  if rg -n '(^|[;&|[:space:]])docker([[:space:]]|$)|docker[._-]compose|(^|[;&|[:space:]])registry[[:space:]_-]*(login|pull|push)([[:space:]]|$)|(^|[;&|[:space:]])kubectl([[:space:]]|$)|(^|[;&|[:space:]])terraform([[:space:]]|$)|shell=True|os\.system\(' $code_paths; then
    echo "AION-240 must not add staging build, registry, deployment, rollback, Kubernetes or Terraform execution" >&2
    exit 1
  fi
  if rg -n '(^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp)\b|urllib\.request|dns\.resolver|getaddrinfo\(|create_connection\()' $code_paths; then
    echo "AION-240 must not add network or DNS execution" >&2
    exit 1
  fi
fi

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

import v02_release_qualification_foundation_operator_evaluation as h

root = Path.cwd()
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
    "examples/v02-release-qualification/staging-qualification-authorization.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    resource_limits = payload.get("resource_limits", {})
    if isinstance(resource_limits, dict) and isinstance(resource_limits.get("limits"), dict):
        resource_limits = resource_limits["limits"]
    prohibited = payload.get("prohibited_capabilities", {})
    if any(prohibited.values()):
        raise SystemExit(f"prohibited staging capability enabled in {relative}")
    zero_keys = payload.get("zero_resource_limit_keys") or list(h.ZERO_AION241_LIMITS)
    for key in zero_keys:
        if resource_limits.get(key) != 0:
            raise SystemExit(f"zero staging limit mismatch in {relative}: {key}")
    post_aion242 = (
        payload.get("active_v02_release_qualification_authorization")
        == "AION-242-V02RQ-0003"
    )
    if post_aion242:
        if payload.get("release_candidate_artifact_build_authorized") is not True:
            raise SystemExit(f"{relative} must authorize only the future release-candidate build")
        if payload.get("release_candidate_created") is not False:
            raise SystemExit(f"{relative} must keep release_candidate_created=false")
        if payload.get("release_candidate_published") is not False:
            raise SystemExit(f"{relative} must keep release_candidate_published=false")
    for flag in (
        "production_runtime_authorized",
        "production_deployment_enabled",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(flag) is not False:
            raise SystemExit(f"{relative} must keep {flag}=false")
    if not post_aion242 and payload.get("release_candidate_creation_enabled") is not False:
        raise SystemExit(f"{relative} must keep release_candidate_creation_enabled=false")
PY

echo "controlled isolated staging qualification authorization no-go PASS"
