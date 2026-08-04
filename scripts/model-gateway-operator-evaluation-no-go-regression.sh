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
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AION235_SOURCE_ALLOWED_STATES = {
    "sandboxed_capability_runtime_implemented_reference_only_pending_closeout": (
        "AION-234-SRI-0003",
        "AION-235",
        "AION-236",
    ),
    "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented": (
        "AION-236-SRI-0004",
        "AION-237",
        "AION-238",
    ),
    "operator_console_integrated_local_runtime_implemented_pending_final_evaluation": (
        "AION-236-SRI-0004",
        "AION-237",
        "AION-238",
    ),
}
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
PROHIBITED_AION235_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py",
    "services/brain-api/src/aion_brain/capability_runtime/",
)
AION237_SOURCE_EXACT = {
    "services/brain-api/src/aion_brain/contracts/operator_console_integration.py",
    "scripts/operator-console-integrated-local-run.py",
    "scripts/operator-console-integration-check.sh",
    "scripts/operator-console-integration-no-go-regression.sh",
    "scripts/operator-console-integrated-pilot-evidence-check.sh",
    "scripts/operator-console-integration-authorization-check.sh",
    "scripts/operator-console-integration-authorization-no-go-regression.sh",
    "scripts/operator-console-integration-runtime-hold.sh",
    "scripts/operator-console-static-check.sh",
    "scripts/static-console-safety-check.sh",
}
AION237_SOURCE_PREFIXES = (
    "services/brain-api/src/aion_brain/operator_console_runtime/",
    "operator-console-static/",
    "docs/",
    "examples/",
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
    return (
        path in AION243_ALLOWED_EXACT
        or path.startswith(AION243_ALLOWED_PREFIXES)
        or aion246_source_allowed(path)
    )


def aion246_source_allowed(path: str) -> bool:
    ledger = ROOT / "docs/adaptive-intelligence/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    return (
        payload.get("program_state")
        == "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
        and payload.get("active_adaptive_intelligence_authorization") == "AION-245-AI-0001"
        and payload.get("active_adaptive_intelligence_task") == "AION-246"
        and payload.get("formal_closeout_task") == "AION-247"
        and payload.get("external_cognition_gateway_implemented") is True
        and payload.get("external_cognition_gateway_state")
        == "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout"
        and (
            path == "services/brain-api/src/aion_brain/contracts/external_cognition.py"
            or path.startswith("services/brain-api/src/aion_brain/external_cognition/")
        )
    )


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


def aion235_implementation_state_active() -> bool:
    ledger = ROOT / "docs/secure-runtime-integration/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    if payload.get("program_state") == "secure_runtime_integration_program_complete":
        return (
            payload.get("sandboxed_capability_runtime_implemented") is True
            and payload.get("active_sri_implementation_authorization_count") == 0
            and payload.get("active_sri_implementation_authorization") is None
            and payload.get("active_sri_implementation_task") is None
            and payload.get("formal_closeout_task") is None
            and payload.get("final_completed_task") == "AION-238"
        )
    expected = AION235_SOURCE_ALLOWED_STATES.get(payload.get("program_state"))
    return (
        expected is not None
        and payload.get("active_sri_implementation_authorization") == expected[0]
        and payload.get("active_sri_implementation_task") == expected[1]
        and payload.get("formal_closeout_task") == expected[2]
        and payload.get("sandboxed_capability_runtime_implemented") is True
    )


def aion237_implementation_state_active() -> bool:
    ledger = ROOT / "docs/secure-runtime-integration/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    if payload.get("program_state") == "secure_runtime_integration_program_complete":
        return (
            payload.get("operator_console_integration_implemented") is True
            and payload.get("integrated_authenticated_local_pilot_completed") is True
            and payload.get("active_sri_implementation_authorization_count") == 0
            and payload.get("active_sri_implementation_authorization") is None
            and payload.get("active_sri_implementation_task") is None
            and payload.get("formal_closeout_task") is None
            and payload.get("final_completed_task") == "AION-238"
        )
    return (
        payload.get("program_state")
        == "operator_console_integrated_local_runtime_implemented_pending_final_evaluation"
        and payload.get("operator_console_integration_implemented") is True
        and payload.get("integrated_authenticated_local_pilot_completed") is True
        and payload.get("active_sri_implementation_authorization") == "AION-236-SRI-0004"
        and payload.get("active_sri_implementation_task") == "AION-237"
        and payload.get("formal_closeout_task") == "AION-238"
    )


aion235_active = aion235_implementation_state_active()
aion237_active = aion237_implementation_state_active()
changed_paths: set[str] = set()
for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"source deletion or rename is not authorized: {parts}")
    for raw_path in paths:
        path = raw_path.replace("\\", "/")
        if aion243_source_allowed(path):
            continue
        changed_paths.add(path)
        if Path(path).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {path}")
        if any(path.startswith(prefix) for prefix in PROHIBITED_AION235_SOURCE):
            if not aion235_active:
                raise SystemExit(
                    f"AION-235 source is not authorized on AION-234 branch: {path}"
                )
            continue
        if path in AION237_SOURCE_EXACT or path.startswith(AION237_SOURCE_PREFIXES):
            if not aion237_active:
                raise SystemExit(f"AION-237 source is not authorized yet: {path}")
            continue
        if path == "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py" or path.startswith(
            "services/brain-api/src/aion_brain/v02_release_qualification/"
        ):
            continue
        if aion241_source_allowed(path):
            continue
        if path.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/dependency path changed: {path}")
        if not allowed_path(path):
            raise SystemExit(f"AION-234 changed disallowed path: {path}")

if not aion235_active:
    for path in PROHIBITED_AION235_SOURCE:
        target = ROOT / path
        if target.exists():
            raise SystemExit(
                f"AION-235 source exists before authorization implementation task: {path}"
            )

if not aion237_active:
    for path in sorted(AION237_SOURCE_EXACT):
        target = ROOT / path
        if target.exists():
            raise SystemExit(f"AION-237 source exists before implementation state: {path}")
    for prefix in AION237_SOURCE_PREFIXES:
        if not prefix.startswith("services/brain-api/src/aion_brain/"):
            continue
        target = ROOT / prefix
        if target.exists():
            raise SystemExit(f"AION-237 source exists before implementation state: {prefix}")

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
