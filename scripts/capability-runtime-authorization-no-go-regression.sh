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
import ast, importlib.util, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(os.environ["AION_REPO_ROOT"])
spec = importlib.util.spec_from_file_location("aion234_eval", ROOT / "scripts/lib/model_gateway_operator_evaluation.py")
h = importlib.util.module_from_spec(spec); sys.modules[spec.name] = h; assert spec.loader is not None; spec.loader.exec_module(h)
ALLOWED_PREFIXES = ("docs/", "examples/", "operator-console-static/", "scripts/", "services/brain-api/tests/")
ALLOWED_EXACT = {"README.md", "AGENTS.md"}
PROHIBITED_PREFIXES = (".github/workflows/", "migrations/", "services/brain-api/migrations/", "infra/postgres/migrations/", "packages/aion-sdk-python/")
PROHIBITED_NAMES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock"}
PROHIBITED_IMPORT_ROOTS = {"aiohttp", "anthropic", "boto3", "botocore", "httpx", "openai", "requests", "socket", "ssl", "urllib", "webbrowser"}
PROHIBITED_CALLS = {"eval", "exec", "__import__", "compile"}
def run(args, check=True): return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)
def ref_exists(ref): return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0
def comparison_base():
    candidates = []
    if os.environ.get("GITHUB_BASE_REF"): candidates.extend([f"origin/{os.environ['GITHUB_BASE_REF']}", os.environ["GITHUB_BASE_REF"]])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge.returncode == 0 and merge.stdout.strip(): return merge.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None
def changed_entries():
    entries = []
    base = comparison_base()
    if base:
        entries += [line.split("\t") for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines() if line.strip()]
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries += [line.split("\t") for line in run(args).stdout.splitlines() if line.strip()]
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "): entries.append(["A", line[3:]])
    return entries
for parts in changed_entries():
    if parts[0].startswith(("D", "R")): raise SystemExit(f"source deletion or rename is not authorized: {parts}")
    for raw in parts[1:]:
        path = raw.replace("\\", "/")
        if Path(path).name in PROHIBITED_NAMES: raise SystemExit(f"dependency/package file changed: {path}")
        if path.startswith(PROHIBITED_PREFIXES): raise SystemExit(f"prohibited release path changed: {path}")
        if path.startswith("services/brain-api/src/aion_brain/"): raise SystemExit(f"runtime source changed on AION-234 branch: {path}")
        if path in h.FUTURE_AION235_SOURCE_SCOPE or path.startswith("services/brain-api/src/aion_brain/capability_runtime/"): raise SystemExit(f"AION-235 source is not authorized on AION-234 branch: {path}")
        if not (path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)): raise SystemExit(f"AION-234 changed disallowed path: {path}")
for path in h.FUTURE_AION235_SOURCE_SCOPE:
    if (ROOT / path).exists(): raise SystemExit(f"AION-235 source exists before implementation task: {path}")
tree = ast.parse((ROOT / "scripts/lib/model_gateway_operator_evaluation.py").read_text(encoding="utf-8"))
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.split(".", 1)[0] in PROHIBITED_IMPORT_ROOTS: raise SystemExit(f"prohibited import in evaluator: {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        if (node.module or "").split(".", 1)[0] in PROHIBITED_IMPORT_ROOTS: raise SystemExit(f"prohibited import in evaluator: {node.module}")
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in PROHIBITED_CALLS:
        raise SystemExit(f"prohibited dynamic execution call in evaluator: {node.func.id}")
for relative in ("docs/secure-runtime-integration/program-ledger.json", "docs/secure-runtime-integration/authorization-ledger.json", "examples/secure-runtime-integration/capability-runtime-authorization.json"):
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    for key in h.PROHIBITED_CAPABILITY_FLAGS:
        if payload.get(key) is not False and payload.get("prohibited_capabilities", {}).get(key) is not False:
            raise SystemExit(f"prohibited capability flag is not false in {relative}: {key}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "sandboxed capability runtime authorization no-go PASS"
