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
publication = root / "examples/v02-release-qualification/v02-rc1-publication-evidence.json"
if not publication.is_file():
    print("AION-244 programme final-complete skeleton PASS")
    raise SystemExit(0)
for relative in (
    "docs/v02-release-qualification/program-ledger.json",
    "docs/v02-release-qualification/authorization-ledger.json",
):
    payload = json.loads((root / relative).read_text(encoding="utf-8"))
    if payload["v02_release_qualification_program_complete"] is not True:
        raise SystemExit(f"{relative} programme complete mismatch")
    if payload["active_v02_release_qualification_authorization_count"] != 0:
        raise SystemExit(f"{relative} active authorization count mismatch")
    if payload["release_candidate_published"] is not True:
        raise SystemExit(f"{relative} candidate publication mismatch")
    if payload["v02_tag_created"] is not True or payload["v02_release_created"] is not True:
        raise SystemExit(f"{relative} RC1 tag/release flags mismatch")
    if payload["v02_stable_tag_created"] is not False or payload["v02_stable_release_created"] is not False:
        raise SystemExit(f"{relative} stable release flags mismatch")
print("AION-244 programme final complete PASS")
PY
