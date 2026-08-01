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
import json
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
AION_237_ALLOWED_PREFIXES = (
    "services/brain-api/src/aion_brain/operator_console_runtime/",
    "operator-console-static/",
    "docs/",
    "examples/",
)
AION_237_ALLOWED_EXACT = {
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


def aion237_implemented() -> bool:
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
        payload.get("operator_console_integration_implemented") is True
        and payload.get("integrated_authenticated_local_pilot_completed") is True
        and payload.get("active_sri_implementation_authorization") == "AION-236-SRI-0004"
        and payload.get("formal_closeout_task") == "AION-238"
    )


aion237_active = aion237_implemented()
if not aion237_active:
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
            allowed_aion237 = (
                aion237_active
                and (path in AION_237_ALLOWED_EXACT or path.startswith(AION_237_ALLOWED_PREFIXES))
            )
            allowed_aion239 = (
                path == "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py"
                or path.startswith("services/brain-api/src/aion_brain/v02_release_qualification/")
            )
            if not (allowed_aion237 or allowed_aion239):
                raise SystemExit(
                    f"runtime source change is not authorized on AION-236 branch: {path}"
                )
        if path.startswith(PROHIBITED_AION_237_SOURCE) and not aion237_active:
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
