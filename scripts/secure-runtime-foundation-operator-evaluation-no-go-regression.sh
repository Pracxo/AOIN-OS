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

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AION235_IMPLEMENTED_STATE = (
    "sandboxed_capability_runtime_implemented_reference_only_pending_closeout"
)
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
AION243_ALLOWED_EXACT = {
    "packages/aion-sdk-python/pyproject.toml",
    "scripts/v02-release-candidate-local-run.py",
    "services/brain-api/pyproject.toml",
    "services/brain-api/src/aion_brain/contracts/v02_release_candidate.py",
}
AION243_ALLOWED_PREFIXES = ("services/brain-api/src/aion_brain/v02_release_candidate/",)
AION233_SOURCE_EXACT = {
    "services/brain-api/src/aion_brain/contracts/model_gateway.py",
    "services/brain-api/src/aion_brain/model_gateway/__init__.py",
    "services/brain-api/src/aion_brain/model_gateway/authorization.py",
    "services/brain-api/src/aion_brain/model_gateway/manifests.py",
    "services/brain-api/src/aion_brain/model_gateway/request_envelope.py",
    "services/brain-api/src/aion_brain/model_gateway/context_budget.py",
    "services/brain-api/src/aion_brain/model_gateway/routing.py",
    "services/brain-api/src/aion_brain/model_gateway/circuit_breaker.py",
    "services/brain-api/src/aion_brain/model_gateway/guard.py",
    "services/brain-api/src/aion_brain/model_gateway/response_validation.py",
    "services/brain-api/src/aion_brain/model_gateway/provider_registry.py",
    "services/brain-api/src/aion_brain/model_gateway/provider_adapter.py",
    "services/brain-api/src/aion_brain/model_gateway/reference_provider.py",
    "services/brain-api/src/aion_brain/model_gateway/audit.py",
    "services/brain-api/src/aion_brain/model_gateway/observability.py",
    "services/brain-api/src/aion_brain/model_gateway/integrity.py",
    "services/brain-api/src/aion_brain/model_gateway/evidence.py",
}
AION235_SOURCE_EXACT = {
    "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py",
}
AION235_SOURCE_PREFIXES = ("services/brain-api/src/aion_brain/capability_runtime/",)
AION237_SOURCE_EXACT = {
    "services/brain-api/src/aion_brain/contracts/operator_console_integration.py",
}
AION237_SOURCE_PREFIXES = ("services/brain-api/src/aion_brain/operator_console_runtime/",)


def aion241_source_allowed(path: str) -> bool:
    ledger = ROOT / "docs/v02-release-qualification/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    if payload.get("controlled_staging_qualification_implemented") is not True:
        return False
    return path in set(payload.get("implemented_source_scope", ())) and (
        path == "services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py"
        or path.startswith("services/brain-api/src/aion_brain/v02_staging_qualification/")
    )


def aion243_source_allowed(path: str) -> bool:
    return path in AION243_ALLOWED_EXACT or path.startswith(AION243_ALLOWED_PREFIXES)


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
        output = run(["git", "diff", "--name-status", base, "HEAD"]).stdout
        entries.extend(line.split("\t") for line in output.splitlines() if line.strip())
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


def aion235_implementation_state_active() -> bool:
    ledger = ROOT / "docs/secure-runtime-integration/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    return (
        payload.get("program_state") == AION235_IMPLEMENTED_STATE
        and payload.get("active_sri_implementation_authorization") == "AION-234-SRI-0003"
        and payload.get("active_sri_implementation_task") == "AION-235"
        and payload.get("formal_closeout_task") == "AION-236"
    )


def aion235_source_allowed(path: str) -> bool:
    return (
        aion235_active
        and (path in AION235_SOURCE_EXACT or path.startswith(AION235_SOURCE_PREFIXES))
    )


def aion237_implementation_state_active() -> bool:
    ledger = ROOT / "docs/secure-runtime-integration/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    return (
        payload.get("program_state")
        == "operator_console_integrated_local_runtime_implemented_pending_final_evaluation"
        and payload.get("operator_console_integration_implemented") is True
        and payload.get("integrated_authenticated_local_pilot_completed") is True
        and payload.get("active_sri_implementation_authorization") == "AION-236-SRI-0004"
        and payload.get("active_sri_implementation_task") == "AION-237"
        and payload.get("formal_closeout_task") == "AION-238"
    )


def aion237_source_allowed(path: str) -> bool:
    return (
        aion237_active
        and (path in AION237_SOURCE_EXACT or path.startswith(AION237_SOURCE_PREFIXES))
    )


aion235_active = aion235_implementation_state_active()
aion237_active = aion237_implementation_state_active()
for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if aion243_source_allowed(normalized):
            continue
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized in AION233_SOURCE_EXACT:
            continue
        if aion235_source_allowed(normalized):
            continue
        if aion237_source_allowed(normalized):
            continue
        if normalized == "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py" or normalized.startswith(
            "services/brain-api/src/aion_brain/v02_release_qualification/"
        ):
            continue
        if aion241_source_allowed(normalized):
            continue
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/dependency path changed: {normalized}")
        if not allowed_path(normalized):
            raise SystemExit(f"AION-232 changed disallowed path: {normalized}")

program = json.loads((ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text())
if program.get("v02_release_ready") is not False:
    raise SystemExit("v02_release_ready must remain false")
if program.get("v02_tag_created") is not False:
    raise SystemExit("v02_tag_created must remain false")
if program.get("v02_release_created") is not False:
    raise SystemExit("v02_release_created must remain false")
PY

aion_confirm_immutable_v01_tag_history >/dev/null

echo "secure runtime foundation operator evaluation no-go PASS"
