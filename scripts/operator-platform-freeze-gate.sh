#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

if [[ "${AION_OPERATOR_PLATFORM_FREEZE_SKIP_REGRESSION:-}" == "1" ]]; then
  echo "PASS: operator platform regression deferred to outer aggregate gate"
else
  ./scripts/operator-platform-regression.sh
fi
git diff --check

git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

echo "Working tree status summary:"
if [[ -n "$(git status --short)" ]]; then
  git status --short
else
  echo "clean"
fi

# aion-v0.1.0 exact-fetch and immutable SHA verification live in scripts/lib/immutable-tags.sh.
aion_confirm_immutable_v01_tag_history >/dev/null

./scripts/static-console-safety-check.sh
./scripts/auth-runtime-check.sh
./scripts/operator-actions-check.sh
./scripts/action-authorization-check.sh
./scripts/provider-dashboard-check.sh
./scripts/module-lifecycle-dashboard-check.sh

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
freeze = json.loads(
    (root / "examples/operator-console/operator-platform-freeze-gate-result.json").read_text()
)
flags = freeze.get("safety_flags", {})
if freeze.get("status") != "passed":
    raise SystemExit("freeze gate example must be passed")
if flags.get("static_console_read_only") is not True:
    raise SystemExit("static console must remain read-only")
for key in (
    "auth_runtime_enabled",
    "production_auth_enabled",
    "write_controls_present",
    "activation_controls_present",
    "execution_controls_present",
    "provider_call_controls_present",
    "external_calls_enabled",
    "frontend_dependencies_present",
    "package_install_allowed",
):
    if flags.get(key) is not False:
        raise SystemExit(f"freeze gate unsafe flag must be false: {key}")

print("Operator platform freeze gate safety flags PASS")
PY

cat <<'SUMMARY'
Operator platform freeze gate result:
- regression_matrix: passed
- whitespace_check: passed
- release_tag_guard: passed
- static_console_read_only: true
- auth_runtime_enabled: false
- write_activation_execution_provider_external_controls_absent: true
Operator platform freeze gate PASS
SUMMARY
