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
import subprocess
from pathlib import Path

root = Path.cwd()
evidence_path = root / "examples/v02-release-qualification/v02-rc1-publication-evidence.json"
if not evidence_path.is_file():
    print("AION-244 RC1 publication check skeleton PASS")
    raise SystemExit(0)
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
required = {
    "task_id": "AION-244",
    "candidate_id": "aion-v0.2.0-rc.1",
    "candidate_source_commit": "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e",
    "tag_name": "aion-v0.2.0-rc.1",
    "tag_target_commit": "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e",
    "release_name": "AION OS v0.2.0-rc.1",
    "release_draft": False,
    "release_prerelease": True,
    "release_asset_count": 24,
    "assets_uploaded": 24,
    "assets_downloaded_for_verification": 24,
    "asset_hash_matches": 24,
    "asset_hash_failures": 0,
    "signature_failures": 0,
    "production_deployments": 0,
    "stable_tags_created": 0,
    "stable_releases_created": 0,
}
for key, value in required.items():
    if evidence.get(key) != value:
        raise SystemExit(f"publication evidence mismatch {key}: {evidence.get(key)!r}")
target = subprocess.run(
    ["git", "rev-parse", "aion-v0.2.0-rc.1^{}"],
    cwd=root,
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
if target != "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e":
    raise SystemExit("RC1 tag target mismatch")
print("AION-244 RC1 publication check PASS")
PY
