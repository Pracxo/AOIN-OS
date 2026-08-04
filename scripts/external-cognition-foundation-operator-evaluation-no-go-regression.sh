#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
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
PROHIBITED_PATHS = {
    "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/__init__.py",
    "scripts/live-provider-pilot-local-run.py",
    "services/brain-api/src/aion_brain/external_cognition/network.py",
    "services/brain-api/src/aion_brain/external_cognition/http_client.py",
    "services/brain-api/src/aion_brain/external_cognition/openai.py",
    "services/brain-api/src/aion_brain/external_cognition/anthropic.py",
    "services/brain-api/src/aion_brain/external_cognition/google.py",
    "services/brain-api/src/aion_brain/external_cognition/azure_openai.py",
    "services/brain-api/src/aion_brain/external_cognition/credential_store.py",
    "services/brain-api/src/aion_brain/external_cognition/token_store.py",
    "services/brain-api/src/aion_brain/external_cognition/background_worker.py",
    "services/brain-api/src/aion_brain/external_cognition/scheduler.py",
    "services/brain-api/src/aion_brain/api/external_cognition.py",
}
PROHIBITED_FILE_NAMES = {
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
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/",
    "packages/aion-sdk-python/src/",
    "packages/aion-sdk-python/aionctl/",
)
ALLOWED_RUNTIME_PREFIX = "services/brain-api/tests/"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if not ref_exists(candidate):
            continue
        merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    if ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


for path in sorted(PROHIBITED_PATHS):
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited AION-247/AION-248 source exists: {path}")

base = comparison_base()
changed: set[str] = set()
if base is not None:
    diff = run(["git", "diff", "--name-only", base, "HEAD"])
    changed = {line.strip() for line in diff.stdout.splitlines() if line.strip()}

for path in sorted(changed):
    name = Path(path).name
    if name in PROHIBITED_FILE_NAMES:
        raise SystemExit(f"package/dependency file change is not authorized: {path}")
    for prefix in PROHIBITED_PREFIXES:
        if path.startswith(prefix) and not path.startswith(ALLOWED_RUNTIME_PREFIX):
            raise SystemExit(f"runtime/dependency/workflow path change is not authorized: {path}")

print("external cognition foundation operator evaluation no-go PASS")
PY
