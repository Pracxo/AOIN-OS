#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path.cwd()
IMPLEMENTED_DISABLED_STATE = (
    "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
)
POST_EVALUATION_STATE = (
    "external_cognition_foundation_evaluated_live_provider_pilot_authorized_not_implemented"
)
IMPLEMENTED_GATEWAY_STATES = {
    "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout",
    "implemented_disabled_deterministic_fixture_only_operator_evaluated_live_provider_pilot_authorized_not_implemented",
}
ALLOWED_CHANGED_PREFIXES = (
    "docs/",
    "examples/",
    "operator-console-static/demo-data/",
    "services/brain-api/tests/",
    "packages/aion-sdk-python/tests/",
    "scripts/",
)
ALLOWED_CHANGED_FILES = {
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/adr/README.md",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/pyproject.toml",
    "operator-console-static/app.js",
    "operator-console-static/index.html",
    "operator-console-static/README.md",
}
AION246_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition/__init__.py",
    "services/brain-api/src/aion_brain/external_cognition/authorization.py",
    "services/brain-api/src/aion_brain/external_cognition/component_binding.py",
    "services/brain-api/src/aion_brain/external_cognition/provider_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/model_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/request_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/response_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/message_normalization.py",
    "services/brain-api/src/aion_brain/external_cognition/structured_output.py",
    "services/brain-api/src/aion_brain/external_cognition/routing_policy.py",
    "services/brain-api/src/aion_brain/external_cognition/budgets.py",
    "services/brain-api/src/aion_brain/external_cognition/trust.py",
    "services/brain-api/src/aion_brain/external_cognition/redaction.py",
    "services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py",
    "services/brain-api/src/aion_brain/external_cognition/fixture_provider.py",
    "services/brain-api/src/aion_brain/external_cognition/replay.py",
    "services/brain-api/src/aion_brain/external_cognition/observability.py",
    "services/brain-api/src/aion_brain/external_cognition/audit.py",
    "services/brain-api/src/aion_brain/external_cognition/integrity.py",
    "services/brain-api/src/aion_brain/external_cognition/evidence.py",
    "scripts/external-cognition-fixture-local-run.py",
}
PROHIBITED_SOURCE = [
    "services/brain-api/src/aion_brain/api/external_cognition.py",
]
PROHIBITED_PROVIDER_FILES = [
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
]


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main", "HEAD~1"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge.returncode == 0 and merge.stdout.strip():
                return merge.stdout.strip()
    return None


def aion246_implementation_state_active() -> bool:
    ledger = ROOT / "docs/adaptive-intelligence/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    return (
        payload.get("program_state") in {IMPLEMENTED_DISABLED_STATE, POST_EVALUATION_STATE}
        and payload.get("external_cognition_gateway_implemented") is True
        and payload.get("external_cognition_gateway_state") in IMPLEMENTED_GATEWAY_STATES
    )


aion246_active = aion246_implementation_state_active()
base = comparison_base()
changed: list[str] = []
if base:
    changed = [
        line.strip()
        for line in run(["git", "diff", "--name-only", base, "HEAD"]).stdout.splitlines()
        if line.strip()
    ]

for path in changed:
    allowed = (
        path in ALLOWED_CHANGED_FILES
        or path.startswith(ALLOWED_CHANGED_PREFIXES)
        or (aion246_active and path in AION246_SOURCE)
    )
    if not allowed:
        raise SystemExit(f"AION-245 changed a prohibited path: {path}")
    if path.startswith("services/brain-api/src/aion_brain/") and not (
        aion246_active and path in AION246_SOURCE
    ):
        raise SystemExit(f"runtime source change is prohibited: {path}")
    if path.startswith("packages/aion-sdk-python/src/"):
        raise SystemExit(f"SDK runtime source change is prohibited: {path}")
    if path.startswith(".github/workflows/"):
        raise SystemExit(f"workflow change is prohibited: {path}")
    if "migration" in path.lower() or path.startswith("migrations/"):
        raise SystemExit(f"migration change is prohibited: {path}")
    if Path(path).name in {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"}:
        raise SystemExit(f"package file change is prohibited: {path}")
    if Path(path).name in {"Dockerfile", "docker-compose.yml"}:
        raise SystemExit(f"container definition change is prohibited: {path}")

if base:
    for pyproject in ("services/brain-api/pyproject.toml", "packages/aion-sdk-python/pyproject.toml"):
        diff = run(["git", "diff", "-U0", base, "HEAD", "--", pyproject]).stdout
        for line in diff.splitlines():
            if not line or line.startswith(("+++", "---", "@@")):
                continue
            if line.startswith(("+", "-")) and "version = " not in line:
                raise SystemExit(f"non-version pyproject change detected in {pyproject}: {line}")

for path in PROHIBITED_PROVIDER_FILES + PROHIBITED_SOURCE:
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited AION-246 source exists during AION-245: {path}")

if aion246_active:
    for path in AION246_SOURCE:
        if not (ROOT / path).is_file():
            raise SystemExit(f"authorized AION-246 source missing: {path}")
else:
    for path in AION246_SOURCE:
        if (ROOT / path).exists():
            raise SystemExit(f"AION-246 source exists before implementation: {path}")

if run(["git", "tag", "--list", "aion-v0.2.0", "v0.2.0*"]).stdout.strip():
    raise SystemExit("stable v0.2 tag exists")
if run(["git", "tag", "--list", "aion-v0.3*", "v0.3*"]).stdout.strip():
    raise SystemExit("v0.3 tag exists")

if shutil.which("gh") is not None and run(["gh", "auth", "status"], check=False).returncode == 0:
    for release_tag in ("aion-v0.2.0", "v0.2.0", "aion-v0.3.0", "v0.3.0"):
        if run(["gh", "release", "view", release_tag], check=False).returncode == 0:
            raise SystemExit(f"prohibited stable release exists: {release_tag}")

print("adaptive intelligence programme authorization no-go PASS")
PY
