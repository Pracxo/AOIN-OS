#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/v02-release-candidate-no-go-regression.sh >/dev/null

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c
from aion_brain.v02_release_candidate import ControlledV02ReleaseCandidateService

root = Path.cwd()
required_docs = (
    "docs/v02-release-qualification/release-candidate-implementation.md",
    "docs/v02-release-qualification/release-candidate-contracts-implementation.md",
    "docs/v02-release-qualification/release-candidate-component-lineage.md",
    "docs/v02-release-qualification/release-candidate-source-snapshot.md",
    "docs/v02-release-qualification/release-candidate-brain-api-image.md",
    "docs/v02-release-qualification/release-candidate-sdk-packages.md",
    "docs/v02-release-qualification/release-candidate-operator-console-bundle.md",
    "docs/v02-release-qualification/release-candidate-sbom.md",
    "docs/v02-release-qualification/release-candidate-provenance.md",
    "docs/v02-release-qualification/release-candidate-checksums.md",
    "docs/v02-release-qualification/release-candidate-qualification-signatures.md",
    "docs/v02-release-qualification/release-candidate-reproducibility.md",
    "docs/v02-release-qualification/release-candidate-compatibility.md",
    "docs/v02-release-qualification/release-candidate-migration-evidence.md",
    "docs/v02-release-qualification/release-candidate-security-review.md",
    "docs/v02-release-qualification/release-candidate-operator-runbook.md",
    "docs/v02-release-qualification/release-candidate-build-report.md",
    "docs/v02-release-qualification/aion-243-checklist.md",
    "docs/adr/0207-deterministic-local-v02-release-candidate-artifact-bundle-build-and-retention.md",
)
for relative in required_docs:
    if not (root / relative).is_file():
        raise SystemExit(f"missing AION-243 documentation: {relative}")
if "0207-deterministic-local-v02-release-candidate-artifact-bundle-build-and-retention.md" not in (
    root / "docs/adr/README.md"
).read_text(encoding="utf-8"):
    raise SystemExit("ADR 0207 is not indexed")
for relative in c.REQUIRED_SOURCE_SCOPE:
    if not (root / relative).is_file():
        raise SystemExit(f"missing AION-243 source scope: {relative}")

service = ControlledV02ReleaseCandidateService()
authorization = c.canonical_authorization_envelope()
service.validate_authorization(authorization)
plan = c.canonical_artifact_plan()
service.validate_artifact_plan(plan)
version = c.canonical_version_manifest()
service.validate_version_manifest(version)

for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    active_authorization = payload.get("active_v02_release_qualification_authorization")
    active_task = payload.get("active_v02_release_qualification_task")
    publication_auth = payload.get("aion_244_publication_authorization", {})
    if active_authorization == c.AUTHORIZATION_TRANSACTION_ID:
        if active_task != c.IMPLEMENTATION_TASK:
            raise SystemExit(f"{relative} active task mismatch")
        if payload.get("authorization_active") is not True:
            raise SystemExit(f"{relative} authorization must remain active")
        if payload.get("authorization_consumed") is not False:
            raise SystemExit(f"{relative} authorization must remain unconsumed")
    elif active_authorization == "AION-244-V02REL-0001":
        if active_task != "AION-244":
            raise SystemExit(f"{relative} AION-244 active task mismatch")
        closeout = payload.get("aion_242_authorization_closeout", {})
        if closeout.get("authorization_transaction_id") != c.AUTHORIZATION_TRANSACTION_ID:
            raise SystemExit(f"{relative} missing AION-242 closeout")
        if closeout.get("authorization_active") is not False:
            raise SystemExit(f"{relative} AION-242 closeout must be inactive")
        if closeout.get("authorization_consumed") is not True:
            raise SystemExit(f"{relative} AION-242 closeout must be consumed")
        if publication_auth.get("authorization_transaction_id") != "AION-244-V02REL-0001":
            raise SystemExit(f"{relative} missing AION-244 publication authorization")
        if publication_auth.get("authorization_active") is not True:
            raise SystemExit(f"{relative} AION-244 publication authorization must be active")
        if publication_auth.get("authorization_consumed") is not False:
            raise SystemExit(f"{relative} AION-244 publication authorization must be unconsumed")
    else:
        raise SystemExit(f"{relative} active authorization mismatch")
    if payload.get("formal_closeout_task") != c.FORMAL_CLOSEOUT_TASK:
        raise SystemExit(f"{relative} closeout task mismatch")
    if payload.get("v02_release_ready") is not False:
        raise SystemExit(f"{relative} must keep v02_release_ready=false")
PY

echo "deterministic v0.2 release candidate artifact build PASS"
