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
import json, os, subprocess
from pathlib import Path
ROOT = Path(os.environ["AION_REPO_ROOT"])
ALLOWED_PREFIXES = ("docs/", "examples/", "operator-console-static/", "scripts/", "services/brain-api/tests/")
ALLOWED_EXACT = {"README.md", "AGENTS.md"}
PROHIBITED_PREFIXES = (".github/workflows/", "services/brain-api/src/aion_brain/", "services/brain-api/pyproject.toml", "packages/aion-sdk-python/", "migrations/", "services/brain-api/migrations/", "infra/postgres/migrations/")
PROHIBITED_NAMES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock"}
AION233_PREFIXES = ("services/brain-api/src/aion_brain/model_gateway/",)
AION233_EXACT = {"services/brain-api/src/aion_brain/contracts/model_gateway.py"}

def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)

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
        entries.extend(line.split("\t") for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines() if line.strip())
    else:
        print("WARN: comparison base unavailable; relying on working tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries

def allowed(path: str) -> bool:
    return path in ALLOWED_EXACT or path.startswith(ALLOWED_PREFIXES)

for parts in changed_entries():
    status = parts[0]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in parts[1:]:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized in AION233_EXACT or normalized.startswith(AION233_PREFIXES):
            raise SystemExit(f"AION-233 runtime source changed on AION-232 branch: {normalized}")
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/dependency path changed: {normalized}")
        if not allowed(normalized):
            raise SystemExit(f"AION-232 changed disallowed path: {normalized}")

program = json.loads((ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/secure-runtime-integration/authorization-ledger.json").read_text())
for payload in (program, auth):
    for key in ("v02_release_ready", "v02_tag_created", "v02_release_created", "actual_model_provider_call_enabled", "provider_network_egress_enabled", "provider_sdk_enabled", "provider_credential_read_enabled", "provider_credential_persistence_enabled", "api_key_persistence_enabled", "token_persistence_enabled", "live_model_session_enabled", "tool_calling_enabled", "function_calling_enabled", "connector_execution_enabled", "actual_tool_execution_enabled", "prompt_persistence_enabled", "model_response_persistence_enabled", "automatic_memory_write_enabled", "production_memory_write_enabled", "production_policy_mutation_enabled", "actual_belief_creation_enabled", "actual_belief_mutation_enabled", "source_rewrite_enabled", "production_deployment_enabled", "model_weight_training_enabled"):
        if payload.get(key) is not False:
            raise SystemExit(f"model-gateway no-go flag must remain false: {key}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null

echo "controlled model gateway authorization no-go PASS"
