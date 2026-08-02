#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import hashlib
from pathlib import Path

from aion_brain.contracts import v02_release_candidate as c

root = Path.cwd()
path = root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
if not path.is_file():
    raise SystemExit("AION-243 committed evidence is absent")
payload = json.loads(path.read_text(encoding="utf-8"))
expected = hashlib.sha256(
    json.dumps(
        {key: value for key, value in payload.items() if key != "report_fingerprint"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()
if payload.get("report_fingerprint") != expected:
    raise SystemExit("AION-243 evidence report fingerprint mismatch")
required = {
    "candidate_id": c.CANDIDATE_LABEL,
    "authorization_id": c.AUTHORIZATION_TRANSACTION_ID,
    "program_id": c.PROGRAM_ID,
    "brain_api_package_version": c.PYTHON_PACKAGE_VERSION,
    "sdk_package_version": c.PYTHON_PACKAGE_VERSION,
    "candidate_bundle_retained": True,
    "candidate_bundle_count": 1,
    "candidate_image_retained": True,
    "candidate_image_count": 1,
    "release_candidate_created": True,
    "release_candidate_published": False,
    "production_deployment": False,
    "v02_release_ready": False,
    "v02_tag_created": False,
    "v02_release_created": False,
    "integrity_passed": True,
}
for key, value in required.items():
    if payload.get(key) != value:
        raise SystemExit(f"AION-243 evidence mismatch {key}: {payload.get(key)!r}")
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
    if payload.get(key) != 0:
        raise SystemExit(f"AION-243 evidence prohibited counter mismatch {key}")
for key, value in payload.items():
    if isinstance(value, str) and "/Users/damilaremerotiwon/.aion/release-candidates" in value:
        raise SystemExit(f"committed evidence contains an absolute candidate root path: {key}")
PY

echo "deterministic v0.2 release candidate evidence PASS"
