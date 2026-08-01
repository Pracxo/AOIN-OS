#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
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
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
PROHIBITED_AION_237_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/operator_console_integration.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/",
    "operator-console-static/live-console.js",
    "scripts/operator-console-integrated-local-run.py",
)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    if os.environ.get("GITHUB_BASE_REF"):
        candidates.extend([f"origin/{os.environ['GITHUB_BASE_REF']}", os.environ["GITHUB_BASE_REF"]])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge.returncode == 0 and merge.stdout.strip():
                return merge.stdout.strip()
    if ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base is not None:
        entries.extend(
            line.split("\t")
            for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines()
            if line.strip()
        )
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


for path in PROHIBITED_AION_237_SOURCE:
    candidate = ROOT / path
    if path.endswith("/"):
        if candidate.is_dir():
            raise SystemExit(f"AION-237 source must not exist on AION-236 branch: {path}")
    elif candidate.exists():
        raise SystemExit(f"AION-237 source must not exist on AION-236 branch: {path}")

for parts in changed_entries():
    if parts[0].startswith(("D", "R")):
        raise SystemExit(f"deletion or rename is not authorized for AION-236 evaluation: {parts}")
    for raw_path in parts[1:]:
        path = raw_path.replace("\\", "/")
        if Path(path).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {path}")
        if path.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited release path changed: {path}")
        if path.startswith("services/brain-api/src/aion_brain/"):
            raise SystemExit(f"runtime source change is not authorized on AION-236 branch: {path}")
        if path.startswith(PROHIBITED_AION_237_SOURCE):
            raise SystemExit(f"AION-237 implementation path changed too early: {path}")
PY

if rg -n "socket\.|serve_forever|HTTPServer|uvicorn|fastapi|fetch\(|XMLHttpRequest|serviceWorker|WebSocket|indexedDB|localStorage\.setItem|sessionStorage\.setItem" \
  scripts/lib/capability_runtime_operator_evaluation.py \
  scripts/capability-runtime-operator-evaluation-check.sh \
  services/brain-api/tests/test_capability_runtime_operator_evaluation.py \
  services/brain-api/tests/test_capability_runtime_evaluation_*.py; then
  echo "ERROR: AION-236 evaluation introduced prohibited live runtime behavior" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "sandboxed capability runtime operator evaluation no-go PASS"
