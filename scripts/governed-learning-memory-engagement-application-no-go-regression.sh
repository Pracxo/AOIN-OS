#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

comparison_base() {
  local candidate merge_base
  if [[ "${1:-}" == "--merged-main" ]]; then
    echo "HEAD~1"
    return 0
  fi
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    for candidate in "origin/${GITHUB_BASE_REF}" "${GITHUB_BASE_REF}"; do
      if git_ref_exists "$candidate"; then
        merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
        [[ -n "$merge_base" ]] && { echo "$merge_base"; return 0; }
      fi
    done
  fi
  for candidate in origin/main main; do
    if git_ref_exists "$candidate"; then
      merge_base="$(git merge-base HEAD "$candidate" 2>/dev/null || true)"
      [[ -n "$merge_base" ]] && { echo "$merge_base"; return 0; }
    fi
  done
  git_ref_exists HEAD~1 && { echo HEAD~1; return 0; }
  return 1
}

if git ls-files '*.db' '*.sqlite' '*.sqlite3' '*-wal' '*-shm' '*.backup' | rg -n '.+'; then
  echo "ERROR: tracked database, WAL, SHM, or backup artifact exists" >&2
  exit 1
fi

if base="$(comparison_base "${1:-}")"; then
  "$PYTHON_BIN" - "$base" <<'PY'
import subprocess
import sys
from pathlib import Path
from scripts.lib.governed_learning_memory_engagement_application import (
    AION226_SOURCE_SCOPE,
    AION226_SUPPORT_SCOPE,
    EngagementApplicationCheckError,
    validate_source_scope,
)

base = sys.argv[1]
changed = subprocess.run(
    ["git", "diff", "--name-status", base, "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
allowed_source = set(AION226_SOURCE_SCOPE) | set(AION226_SUPPORT_SCOPE)
allowed_prefixes = (
    "docs/",
    "examples/governed-learning-memory/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
blocked_prefixes = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/knowledge_intelligence/",
    "packages/aion-sdk-python/src/",
)
blocked_exact = {
    "services/brain-api/pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
for line in changed:
    parts = line.split("\t")
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"ERROR: deletion or rename is not allowed: {line}")
    for path in paths:
        if path in blocked_exact or path.startswith(blocked_prefixes):
            raise SystemExit(f"ERROR: protected surface changed: {path}")
        if path.startswith("services/brain-api/src/aion_brain/") and path not in allowed_source:
            raise SystemExit(f"ERROR: unauthorized runtime source changed: {path}")
        if not (path in allowed_source or path.startswith(allowed_prefixes) or path in {"README.md", "AGENTS.md"}):
            raise SystemExit(f"ERROR: unexpected AION-226 changed path: {path}")
try:
    validate_source_scope(Path("."))
except EngagementApplicationCheckError as exc:
    raise SystemExit(f"ERROR: {exc}") from exc
PY
fi

if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi
aion_confirm_immutable_v01_tag_history >/dev/null
echo "governed learning memory engagement application no-go PASS"
