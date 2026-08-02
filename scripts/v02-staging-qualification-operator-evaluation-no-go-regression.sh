#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

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

changed_paths_without_aion243() {
  changed_paths | while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    if ! aion243_is_scoped_v02_release_candidate_artifact_build_path "$path"; then
      printf '%s\n' "$path"
    fi
  done
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/adr/0206-controlled-staging-evaluation-and-deterministic-v02-release-candidate-artifact-build-authorization.md|\
    docs/adr/README.md|\
    docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/project-status.md|docs/visual-brain.md|\
    docs/v02-release-qualification/*|\
    docs/release/v02-staging-qualification-operator-evaluation-*|\
    docs/release/v02-release-candidate-*|\
    examples/v02-release-qualification/*|\
    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
    operator-console-static/demo-data/v02-release-qualification-program-authorization.json|\
    operator-console-static/demo-data/v02-release-qualification-staging-authorization.json|\
    operator-console-static/demo-data/v02-staging-qualification-authorization.json|\
    operator-console-static/demo-data/v02-staging-operator-evaluation.json|\
    operator-console-static/demo-data/v02-release-candidate-authorization.json|\
    scripts/auth-design-check.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/lib/v02_staging_qualification_operator_evaluation.py|\
    scripts/v02-staging-qualification-operator-evaluation-check.sh|\
    scripts/v02-staging-qualification-operator-evaluation-no-go-regression.sh|\
    scripts/v02-release-candidate-authorization-check.sh|\
    scripts/v02-release-candidate-authorization-no-go-regression.sh|\
    scripts/v02-release-candidate-runtime-hold.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/v02-release-qualification-program-authorization-check.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-authorization-check.sh|\
    scripts/v02-staging-qualification-authorization-no-go-regression.sh|\
    scripts/v02-staging-qualification-check.sh|\
    scripts/v02-staging-qualification-no-go-regression.sh|\
    scripts/v02-staging-qualification-runtime-hold.sh|\
    scripts/v02-release-qualification-foundation-check.sh|\
    scripts/v02-release-qualification-foundation-operator-evaluation-check.sh|\
    scripts/v02-release-qualification-foundation-runtime-hold.sh|\
    services/brain-api/tests/test_secure_runtime_integration_final_closeout_aion238.py|\
    services/brain-api/tests/test_v02_release_qualification_pilot_evidence_aion239.py|\
    services/brain-api/tests/test_v02_staging_qualification_operator_evaluation_aion242.py)
      return 0
      ;;
  esac
  return 1
}

changed_paths_without_aion243 | sort -u | while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if ! is_allowed_path "$path"; then
    echo "AION-242 changed path outside staging operator-evaluation boundary: $path" >&2
    exit 1
  fi
done

if changed_paths_without_aion243 | sort -u | rg -n '^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-242 must not modify GitHub workflows" >&2
  exit 1
fi
if changed_paths_without_aion243 | sort -u | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|pyproject\.toml)$' >/dev/null 2>&1; then
  echo "AION-242 must not modify package manifests, versions or lockfiles" >&2
  exit 1
fi
if changed_paths_without_aion243 | sort -u | rg -n '(^migrations/|/migrations/)' >/dev/null 2>&1; then
  echo "AION-242 must not add migrations" >&2
  exit 1
fi
if changed_paths_without_aion243 | sort -u | rg -n '^services/brain-api/src/aion_brain/' >/dev/null 2>&1; then
  echo "AION-242 primary branch must not modify runtime source" >&2
  exit 1
fi
if changed_paths_without_aion243 | sort -u | rg -n '^packages/aion-sdk-python/src/' >/dev/null 2>&1; then
  echo "AION-242 primary branch must not modify SDK runtime source" >&2
  exit 1
fi
if changed_paths_without_aion243 | sort -u | rg -n '^services/brain-api/src/aion_brain/(contracts/)?v02_release_candidate|^services/brain-api/src/aion_brain/v02_release_candidate/|^scripts/v02-release-candidate-local-run\.py$' >/dev/null 2>&1; then
  echo "AION-242 must not create AION-243 release-candidate source" >&2
  exit 1
fi

code_changes="$(
  changed_paths_without_aion243 \
    | sort -u \
    | rg -n '^(scripts/.*(\.sh|\.py)|services/brain-api/tests/.*\.py)$' \
    | cut -d: -f2- \
    | rg -v 'no-go-regression\.sh$' \
    || true
)"
if [[ -n "$code_changes" ]]; then
  if rg -n '(^|[;&|[:space:]])docker[[:space:]]+(build|run|login|pull|push|compose|prune|rm|start|stop|down|up)\b|docker[._-]compose|subprocess\..*shell=True|os\.system\(' $code_changes; then
    echo "AION-242 must not add Docker/build/deployment mutation code" >&2
    exit 1
  fi
  if rg -n '(^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp)\b|urllib\.request|dns\.resolver|getaddrinfo\(|create_connection\()' $code_changes; then
    echo "AION-242 must not add network or DNS execution code" >&2
    exit 1
  fi
fi

secret_scan_paths="$(
  changed_paths \
    | sort -u \
    | rg -v '^scripts/.*no-go-regression\.sh$' \
    || true
)"
if [[ -n "$secret_scan_paths" ]]; then
  if rg -n '(^|[^A-Za-z0-9])sk-[A-Za-z0-9]{12,}|ghp_[A-Za-z0-9]{12,}|xoxb-[A-Za-z0-9-]{8,}|-----BEGIN PRIVATE KEY-----|client_secret[[:space:]]*=' $secret_scan_paths; then
    echo "AION-242 must not add credential or token material" >&2
    exit 1
  fi
fi

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

import v02_staging_qualification_operator_evaluation as eval242

root = Path.cwd()
aion243_evidence_exists = (
    root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
).is_file()
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
    if aion243_evidence_exists:
        if payload.get("release_candidate_artifact_build_implemented") is not True:
            raise SystemExit(f"{relative} AION-243 local release-candidate build state missing")
        if payload.get("release_candidate_created") is not True:
            raise SystemExit(f"{relative} AION-243 local release candidate state missing")
        if payload.get("release_candidate_published") is not False:
            raise SystemExit(f"{relative} AION-243 release candidate must remain unpublished")
if not aion243_evidence_exists:
    for path in eval242.FUTURE_AION243_SOURCE_SCOPE:
        if (root / path).exists():
            raise SystemExit(f"AION-243 source exists before authorization is consumed: {path}")
    if (root / eval242.FUTURE_AION243_RUNNER).exists():
        raise SystemExit("AION-243 runner exists before authorization is consumed")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "controlled isolated staging qualification operator evaluation no-go PASS"
