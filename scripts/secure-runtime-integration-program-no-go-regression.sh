#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

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
  if git_ref_exists HEAD^2 && git_ref_exists HEAD^1; then
    echo "HEAD^1"
    return 0
  fi
  if git_ref_exists HEAD~1; then
    echo "HEAD~1"
    return 0
  fi
  return 1
}

is_allowed_path() {
  case "$1" in
    README.md|AGENTS.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/secure-runtime-integration-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0194-secure-runtime-integration-program-charter-and-local-operator-runtime-foundation-authorization.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/*|\
	    operator-console-static/index.html|operator-console-static/app.js|operator-console-static/README.md|\
	    operator-console-static/demo-data/secure-runtime-integration-*.json|\
	    scripts/auth-design-check.sh|\
	    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
	    scripts/operator-console-static-check.sh|\
	    scripts/static-console-safety-check.sh|\
	    scripts/secure-runtime-integration-program-authorization-check.sh|\
	    scripts/secure-runtime-integration-program-no-go-regression.sh|\
	    scripts/secure-runtime-integration-runtime-hold.sh|\
	    scripts/governed-learning-memory-program-final-evaluation-no-go-regression.sh|\
    services/brain-api/tests/test_secure_runtime_integration_*.py)
      return 0
      ;;
  esac
  return 1
}

base_ref="$(comparison_base || true)"
changed_file_list="$(mktemp)"
changed_status_list="$(mktemp)"
trap 'rm -f "$changed_file_list" "$changed_status_list"' EXIT

if [[ -n "$base_ref" ]]; then
  {
    git diff --name-only "$base_ref" HEAD --
    git diff --name-only HEAD --
    git diff --cached --name-only --
    git ls-files --others --exclude-standard --
  } | sort -u > "$changed_file_list"
  {
    git diff --name-status "$base_ref" HEAD --
    git diff --name-status HEAD --
    git diff --cached --name-status --
    git ls-files --others --exclude-standard -- | sed 's/^/A\t/'
  } | sort -u > "$changed_status_list"
else
  {
    git diff --name-only HEAD --
    git diff --cached --name-only --
    git ls-files --others --exclude-standard --
  } | sort -u > "$changed_file_list"
  {
    git diff --name-status HEAD --
    git diff --cached --name-status --
    git ls-files --others --exclude-standard -- | sed 's/^/A\t/'
  } | sort -u > "$changed_status_list"
fi

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  if ! is_allowed_path "$path"; then
    echo "ERROR: AION-230 changed disallowed path: $path" >&2
    exit 1
  fi
  case "$path" in
    services/brain-api/src/*|packages/*|.github/workflows/*|\
    *migrations*|*package.json|*package-lock.json|*pnpm-lock.yaml|*yarn.lock|\
    *poetry.lock|*Pipfile.lock|*requirements*.txt|*pyproject.toml)
      echo "ERROR: prohibited runtime/dependency/migration path changed: $path" >&2
      exit 1
      ;;
  esac
done < "$changed_file_list"

while IFS=$'\t' read -r status path rest; do
  [[ -n "${status:-}" ]] || continue
  if [[ "$status" == D* || "$status" == R* ]]; then
    case "$path" in
      services/brain-api/src/*|packages/*|scripts/*)
        echo "ERROR: prohibited source/script deletion or rename: $status $path ${rest:-}" >&2
        exit 1
      ;;
    esac
  fi
done < "$changed_status_list"

future_source_paths=(
  services/brain-api/src/aion_brain/contracts/secure_runtime.py
  services/brain-api/src/aion_brain/secure_runtime/__init__.py
  services/brain-api/src/aion_brain/secure_runtime/authorization.py
  services/brain-api/src/aion_brain/secure_runtime/identity_binding.py
  services/brain-api/src/aion_brain/secure_runtime/session_lifecycle.py
  services/brain-api/src/aion_brain/secure_runtime/request_pipeline.py
  services/brain-api/src/aion_brain/secure_runtime/capability_dispatch.py
  services/brain-api/src/aion_brain/secure_runtime/runtime_guard.py
  services/brain-api/src/aion_brain/secure_runtime/kill_switch.py
  services/brain-api/src/aion_brain/secure_runtime/audit.py
  services/brain-api/src/aion_brain/secure_runtime/observability.py
  services/brain-api/src/aion_brain/secure_runtime/integrity.py
  services/brain-api/src/aion_brain/secure_runtime/evidence.py
)
for path in "${future_source_paths[@]}"; do
  if [[ -e "$path" ]]; then
    echo "ERROR: AION-231 source exists during AION-230: $path" >&2
    exit 1
  fi
done
if [[ -d services/brain-api/src/aion_brain/secure_runtime ]]; then
  echo "ERROR: secure_runtime source package exists during AION-230" >&2
  exit 1
fi

if grep -R -n '"implementation_approved"[[:space:]]*:[[:space:]]*true' \
  docs/secure-runtime-integration examples/secure-runtime-integration operator-console-static/demo-data/secure-runtime-integration-*.json; then
  echo "ERROR: future implementation approval flag created" >&2
  exit 1
fi

./scripts/secure-runtime-integration-program-authorization-check.sh
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "secure runtime integration program no-go PASS"
