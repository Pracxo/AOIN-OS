#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/v02-production-auth-scan-exclusions.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

comparison_base() {
  if git rev-parse --verify --quiet origin/main >/dev/null; then
    printf '%s\n' "origin/main"
    return 0
  fi
  if git rev-parse --verify --quiet main >/dev/null; then
    printf '%s\n' "main"
    return 0
  fi
  printf '%s\n' "HEAD~1"
}

BASE="$(comparison_base)"
CHANGED="$(git diff --name-only "$BASE"...HEAD -- 2>/dev/null || true)"

if printf '%s\n' "$CHANGED" | rg -n '(^|/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|poetry\.lock|requirements.*\.txt)$' >/dev/null 2>&1; then
  echo "AION-243 must not add package manager or lock files" >&2
  exit 1
fi
if printf '%s\n' "$CHANGED" | rg -n '(^|/)(Dockerfile|docker-compose\.yml|docker-compose\.yaml)$|^\.github/workflows/' >/dev/null 2>&1; then
  echo "AION-243 must not modify Dockerfiles, Compose files or workflows" >&2
  exit 1
fi
if printf '%s\n' "$CHANGED" | rg -n '(^|/)(migrations|alembic)/|(^|/)versions/.*\.py$' >/dev/null 2>&1; then
  echo "AION-243 must not add migrations" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - "$BASE" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c

root = Path.cwd()
base = sys.argv[1]
changed = {
    line.strip()
    for line in subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()
    if line.strip()
}
ledger_path = root / "docs/adaptive-intelligence/program-ledger.json"
aion246_allowed = {
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition/__init__.py",
    "services/brain-api/src/aion_brain/external_cognition/audit.py",
    "services/brain-api/src/aion_brain/external_cognition/authorization.py",
    "services/brain-api/src/aion_brain/external_cognition/budgets.py",
    "services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py",
    "services/brain-api/src/aion_brain/external_cognition/component_binding.py",
    "services/brain-api/src/aion_brain/external_cognition/evidence.py",
    "services/brain-api/src/aion_brain/external_cognition/fixture_provider.py",
    "services/brain-api/src/aion_brain/external_cognition/integrity.py",
    "services/brain-api/src/aion_brain/external_cognition/message_normalization.py",
    "services/brain-api/src/aion_brain/external_cognition/model_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/observability.py",
    "services/brain-api/src/aion_brain/external_cognition/provider_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/redaction.py",
    "services/brain-api/src/aion_brain/external_cognition/replay.py",
    "services/brain-api/src/aion_brain/external_cognition/request_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/response_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/routing_policy.py",
    "services/brain-api/src/aion_brain/external_cognition/structured_output.py",
    "services/brain-api/src/aion_brain/external_cognition/trust.py",
}
if ledger_path.exists():
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if (
        ledger.get("program_state")
        == "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
        and ledger.get("active_adaptive_intelligence_authorization") == "AION-245-AI-0001"
        and ledger.get("active_adaptive_intelligence_task") == "AION-246"
        and ledger.get("formal_closeout_task") == "AION-247"
        and ledger.get("external_cognition_gateway_implemented") is True
        and ledger.get("external_cognition_gateway_state")
        == "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout"
    ):
        changed -= aion246_allowed
allowed_runtime = set(c.REQUIRED_SOURCE_SCOPE) - {"scripts/v02-release-candidate-local-run.py"}
runtime_changes = {
    path
    for path in changed
    if path.startswith("services/brain-api/src/aion_brain/")
    and path not in allowed_runtime
}
if runtime_changes:
    raise SystemExit(f"unauthorized runtime source changes: {sorted(runtime_changes)}")

pyprojects = {
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/pyproject.toml",
}
for pyproject in changed & pyprojects:
    diff = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...HEAD", "--", pyproject],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()
    for line in diff:
        if not line or line.startswith(("+++", "---", "@@")):
            continue
        if line[0] in "+-" and not line[1:].strip().startswith("version = "):
            raise SystemExit(f"{pyproject} changed outside the version line")

for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
    "examples/v02-release-qualification/release-candidate-authorization.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    rc1_published = (root / "examples/v02-release-qualification/v02-rc1-publication-evidence.json").exists()
    if rc1_published:
        for key in (
            "production_runtime_authorized",
            "production_deployment_enabled",
            "release_candidate_promoted",
            "v02_stable_tag_created",
            "v02_stable_release_created",
        ):
            if payload.get(key, False) is not False:
                raise SystemExit(f"{relative} no-go mismatch {key}: {payload.get(key)!r}")
        if relative != "examples/v02-release-qualification/release-candidate-authorization.json":
            for key in ("release_candidate_published", "v02_tag_created", "v02_release_created"):
                if payload.get(key) is not True:
                    raise SystemExit(f"{relative} RC1 publication mismatch {key}: {payload.get(key)!r}")
        continue
    for key in (
        "release_candidate_published",
        "release_candidate_promoted",
        "production_runtime_authorized",
        "production_deployment_enabled",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key, False) is not False:
            raise SystemExit(f"{relative} no-go mismatch {key}: {payload.get(key)!r}")

evidence_path = root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
if evidence_path.exists():
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    for key in (
        "registry_logins",
        "registry_pulls",
        "registry_pushes",
        "public_network_calls",
        "dns_resolutions",
        "public_package_uploads",
        "production_deployments",
        "private_qualification_keys_retained",
    ):
        if evidence.get(key) != 0:
            raise SystemExit(f"candidate evidence no-go mismatch {key}: {evidence.get(key)!r}")
    if evidence.get("candidate_root_path_retained") is not False:
        raise SystemExit("committed evidence must not retain the absolute candidate root")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then
  echo "ERROR: stable v0.2 tag exists" >&2
  exit 1
fi

echo "deterministic v0.2 release candidate artifact build no-go PASS"
