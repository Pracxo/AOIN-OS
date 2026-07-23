#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
ALLOWED_PREFIXES = ("docs/", "examples/", "operator-console-static/", "scripts/", "services/brain-api/tests/")
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
PROHIBITED_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        candidates.extend([f"origin/{base_ref}", base_ref])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None


entries: list[list[str]] = []
base = comparison_base()
if base:
    entries.extend(line.split("\t") for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines() if line.strip())
else:
    print("WARN: comparison base unavailable; relying on current-tree checks")
entries.extend(line.split("\t") for line in run(["git", "diff", "--name-status"]).stdout.splitlines() if line.strip())
entries.extend(line.split("\t") for line in run(["git", "diff", "--cached", "--name-status"]).stdout.splitlines() if line.strip())
for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
    if line.startswith("?? "):
        entries.append(["A", line[3:]])

for parts in entries:
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized.startswith(PROHIBITED_PREFIXES) and normalized not in ALLOWED_EXACT:
            raise SystemExit(f"runtime/source/workflow path changed on AION-206: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            raise SystemExit(f"path outside AION-206 scope: {normalized}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
PY

HARNESS="scripts/lib/knowledge_intelligence_research_operator_evaluation.py"
test -f "$HARNESS"

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|subprocess|git|github)([[:space:].]|$)' "$HARNESS"; then
  echo "ERROR: prohibited network/Git import detected in AION-206 harness" >&2
  exit 1
fi

if rg -n '(knowledge_candidate_created[[:space:]]*=[[:space:]]*True|belief_created[[:space:]]*=[[:space:]]*True|approval_created[[:space:]]*=[[:space:]]*True|authorization_created[[:space:]]*=[[:space:]]*True|runtime_effect[[:space:]]*=[[:space:]]*True)' "$HARNESS"; then
  echo "ERROR: AION-206 harness attempts to create forbidden effects" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "knowledge intelligence research operator evaluation no-go PASS"
