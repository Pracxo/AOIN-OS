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

import shutil
import subprocess
from pathlib import Path

ROOT = Path.cwd()
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
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/pyproject.toml",
    "operator-console-static/README.md",
}
PROHIBITED_SOURCE = [
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition",
    "services/brain-api/src/aion_brain/api/external_cognition.py",
    "scripts/external-cognition-fixture-local-run.py",
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
    for candidate in ("origin/main", "main", "HEAD~1"):
        if ref_exists(candidate):
            merge = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge.returncode == 0 and merge.stdout.strip():
                return merge.stdout.strip()
    return None


base = comparison_base()
changed: list[str] = []
if base:
    changed = [
        line.strip()
        for line in run(["git", "diff", "--name-only", base, "HEAD"]).stdout.splitlines()
        if line.strip()
    ]

for path in changed:
    allowed = path in ALLOWED_CHANGED_FILES or path.startswith(ALLOWED_CHANGED_PREFIXES)
    if not allowed:
        raise SystemExit(f"AION-245 changed a prohibited path: {path}")
    if path.startswith("services/brain-api/src/aion_brain/"):
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

for path in PROHIBITED_SOURCE + PROHIBITED_PROVIDER_FILES:
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited AION-246 source exists during AION-245: {path}")

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
