#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

root = Path.cwd()
auth_path = root / "examples/v02-release-qualification/v02-rc1-publication-authorization.json"
if not auth_path.is_file():
    print("AION-244 RC1 publication authorization skeleton PASS")
    raise SystemExit(0)
auth = json.loads(auth_path.read_text(encoding="utf-8"))
if auth["authorization_transaction_id"] != "AION-244-V02REL-0001":
    raise SystemExit("publication authorization ID mismatch")
if auth["candidate_id"] != "aion-v0.2.0-rc.1":
    raise SystemExit("publication authorization candidate mismatch")
if auth["tag_target_commit"] != "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e":
    raise SystemExit("publication authorization tag target mismatch")
if auth["release_prerelease"] is not True or auth["release_stable"] is not False:
    raise SystemExit("publication authorization release semantics mismatch")
if auth["maximum_annotated_tags_created"] != 1 or auth["maximum_github_prereleases_created"] != 1:
    raise SystemExit("publication authorization single-use limits mismatch")
for key in (
    "maximum_stable_tags_created",
    "maximum_stable_releases_created",
    "maximum_registry_logins",
    "maximum_registry_pushes",
    "maximum_public_package_uploads",
    "maximum_production_deployments",
):
    if auth[key] != 0:
        raise SystemExit(f"publication authorization zero limit mismatch: {key}")
print("AION-244 RC1 publication authorization PASS")
PY
