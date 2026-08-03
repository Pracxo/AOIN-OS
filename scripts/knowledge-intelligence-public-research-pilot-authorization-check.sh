#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
./scripts/knowledge-intelligence-public-research-pilot-authorization-no-go-regression.sh
PYTHONPATH="$ROOT_DIR/scripts/lib:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import os
from pathlib import Path
import knowledge_intelligence_public_research_pilot_authorization as auth
auth.validate_authorization_files(Path(os.environ["AION_REPO_ROOT"]))
PY
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then echo "ERROR: v0.2 tag exists" >&2; exit 1; fi
echo "knowledge intelligence public research pilot authorization PASS"
