#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/operator-console/static-console-ux-refinement.md
  docs/operator-console/static-console-accessibility-checklist.md
  docs/operator-console/static-console-navigation-model.md
  docs/operator-console/static-console-information-architecture.md
  docs/adr/0094-static-console-ux-refinement.md
)

for file in "${required_docs[@]}"; do
  test -f "$file" || {
    echo "missing static console UX doc: $file" >&2
    exit 1
  }
done

grep -q "0094-static-console-ux-refinement.md" docs/adr/README.md || {
  echo "ADR 0094 is not indexed" >&2
  exit 1
}

required_examples=(
  examples/operator-console/static-console-navigation-map.json
  examples/operator-console/static-console-accessibility-check-result.json
)

for file in "${required_examples[@]}"; do
  test -f "$file" || {
    echo "missing static console UX example: $file" >&2
    exit 1
  }
done

grep -q 'class="skip-link"' operator-console-static/index.html || {
  echo "skip link missing from static console" >&2
  exit 1
}

grep -q 'id="console-main"' operator-console-static/index.html || {
  echo "skip link target missing from static console" >&2
  exit 1
}

for group in \
  "Platform" \
  "Modules" \
  "Providers" \
  "Actions" \
  "Auth and Sessions" \
  "Evidence" \
  "Safety"; do
  grep -q "$group" operator-console-static/index.html || {
    echo "navigation group missing: $group" >&2
    exit 1
  }
done

for banner in \
  "read-only" \
  "no activation" \
  "no execution" \
  "no provider calls" \
  "no login" \
  "no credentials"; do
  grep -i -q "$banner" operator-console-static/index.html || {
    echo "static console banner missing: $banner" >&2
    exit 1
  }
done

if rg -n 'method:[[:space:]]*["'\''](PUT|PATCH|DELETE)["'\'']' operator-console-static/app.js; then
  echo "write HTTP method found in app.js" >&2
  exit 1
fi

for required in \
  "isLocalApiOrigin" \
  "apiAllowed: false" \
  'parsed.hostname === "localhost"' \
  'parsed.hostname === "127.0.0.1"' \
  "SAFE_COPY_COMMANDS" \
  "safety-blockers-control"; do
  grep -q "$required" operator-console-static/app.js operator-console-static/index.html || {
    echo "static UX required marker missing: $required" >&2
    exit 1
  }
done

if rg -n 'https?://' operator-console-static/app.js | rg -v 'localhost|127\.0\.0\.1'; then
  echo "non-local URL found in app.js" >&2
  exit 1
fi

if rg -n 'fetch\([[:space:]]*["'\''](https?:)?//' operator-console-static/app.js; then
  echo "external URL fetch found in app.js" >&2
  exit 1
fi

if rg -n 'localStorage|sessionStorage' operator-console-static/app.js; then
  echo "browser storage usage found in app.js" >&2
  exit 1
fi

if rg -n '@import|url\([[:space:]]*["'\'']?https?://' operator-console-static/styles.css; then
  echo "external CSS import found" >&2
  exit 1
fi

grep -q ':focus-visible' operator-console-static/styles.css || {
  echo "focus-visible style missing" >&2
  exit 1
}

grep -q -- '--focus' operator-console-static/styles.css || {
  echo "focus color token missing" >&2
  exit 1
}

for file in \
  package.json \
  package-lock.json \
  pnpm-lock.yaml \
  yarn.lock \
  bun.lockb; do
  test ! -e "$file" || {
    echo "frontend package file is not allowed: $file" >&2
    exit 1
  }
done

if find . -maxdepth 2 -type f \( \
  -name 'vite.config.*' -o \
  -name 'next.config.*' -o \
  -name 'tailwind.config.*' -o \
  -name 'webpack.config.*' \
\) | rg -n '.'; then
  echo "frontend build config is not allowed" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add' \
  operator-console-static docs/operator-console/static-console-ux-refinement.md docs/adr/0094-static-console-ux-refinement.md; then
  echo "package install instruction found" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
nav = json.loads((root / "examples/operator-console/static-console-navigation-map.json").read_text())
accessibility = json.loads(
    (root / "examples/operator-console/static-console-accessibility-check-result.json").read_text()
)
html = (root / "operator-console-static/index.html").read_text()
app = (root / "operator-console-static/app.js").read_text()

expected_groups = {
    "Platform",
    "Modules",
    "Providers",
    "Actions",
    "Auth and Sessions",
    "Evidence",
    "Safety",
}
groups = {group["name"] for group in nav.get("groups", [])}
missing = expected_groups - groups
if missing:
    raise SystemExit(f"navigation map missing groups: {sorted(missing)}")

if nav.get("status") != "passed":
    raise SystemExit("navigation map status must be passed")

for group in nav["groups"]:
    if not group.get("views"):
        raise SystemExit(f"navigation group has no views: {group['name']}")

allowed = {
    "./scripts/ui-release-gate.sh",
    "./scripts/static-console-safety-check.sh",
    "./scripts/operator-platform-regression.sh",
    "./scripts/operator-platform-freeze-gate.sh",
    "./scripts/connector-platform-regression.sh",
    "./scripts/connector-platform-stabilization-gate.sh",
    "./scripts/platform-integration-checkpoint.sh",
    "./scripts/platform-integration-freeze-check.sh",
    "./scripts/platform-integration-no-go-regression.sh",
    "./scripts/post-v01-release-candidate-gate.sh",
    "./scripts/post-v01-release-candidate-freeze.sh",
    "./scripts/post-v01-release-candidate-no-go-regression.sh",
    "./scripts/docs-check.sh",
}
listed = set(nav.get("safe_copy_commands", []))
if listed != allowed:
    raise SystemExit("navigation map safe copy command allowlist mismatch")

commands = set(re.findall(r'data-command="([^"]+)"', html))
if commands != allowed:
    raise SystemExit("static command card allowlist mismatch")

for command in allowed:
    if command not in app:
        raise SystemExit(f"safe copy command missing from app.js: {command}")

if accessibility.get("expected_status") != "passed":
    raise SystemExit("accessibility check result must be passed")
checks = accessibility.get("checks", [])
if not checks or any(item.get("expected_status") != "passed" for item in checks):
    raise SystemExit("accessibility checks must all be passed")

serialized = json.dumps([nav, accessibility], sort_keys=True).lower()
blocked_markers = (
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
    "password",
    "private_key",
    "api_key",
    "authorization",
    "bearer ",
    "sk-",
    "ghp_",
    "xoxb-",
)
for marker in blocked_markers:
    if marker in serialized:
        raise SystemExit(f"unsafe UX example marker found: {marker}")

for key, expected in nav["forbidden_surface"].items():
    if expected is not False:
        raise SystemExit(f"forbidden surface must be false: {key}")

if accessibility.get("write_actions_present") is not False:
    raise SystemExit("write actions must be absent")
if accessibility.get("external_calls_present") is not False:
    raise SystemExit("external calls must be absent")

print("Static console UX JSON checks PASS")
PY

echo "Static console UX check PASS"
