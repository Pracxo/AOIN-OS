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

import ast
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
ALLOWED_PREFIXES = (
    "docs/",
    "examples/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
ALLOWED_EXACT = {"README.md", "AGENTS.md"}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/",
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
PROHIBITED_AION235_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/",
)
PROHIBITED_IMPORT_ROOTS = {
    "aiohttp",
    "anthropic",
    "boto3",
    "botocore",
    "httpx",
    "importlib",
    "openai",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "webbrowser",
}
PROHIBITED_CALLS = {"eval", "exec", "__import__", "compile"}


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
        if ref_exists(candidate):
            merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base:
        entries.extend(
            line.split("\t")
            for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines()
            if line.strip()
        )
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


def allowed_path(path: str) -> bool:
    return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)


changed_paths: set[str] = set()
for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"source deletion or rename is not authorized: {parts}")
    for raw_path in paths:
        path = raw_path.replace("\\", "/")
        changed_paths.add(path)
        if Path(path).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {path}")
        if any(path.startswith(prefix) for prefix in PROHIBITED_AION235_SOURCE):
            raise SystemExit(f"AION-235 source is not authorized on AION-234 branch: {path}")
        if path.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/dependency path changed: {path}")
        if not allowed_path(path):
            raise SystemExit(f"AION-234 changed disallowed path: {path}")

for path in PROHIBITED_AION235_SOURCE:
    target = ROOT / path
    if target.exists():
        raise SystemExit(f"AION-235 source exists before authorization implementation task: {path}")

harness = ROOT / "scripts/lib/model_gateway_operator_evaluation.py"
if harness.exists():
    tree = ast.parse(harness.read_text(encoding="utf-8"), filename=str(harness))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in PROHIBITED_IMPORT_ROOTS:
                    raise SystemExit(f"prohibited import in evaluator: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if root in PROHIBITED_IMPORT_ROOTS:
                raise SystemExit(f"prohibited import in evaluator: {module}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in PROHIBITED_CALLS:
                raise SystemExit(f"prohibited dynamic execution call in evaluator: {func.id}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null

echo "controlled model gateway operator evaluation no-go PASS"
