#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  operator-console-static/README.md
  operator-console-static/index.html
  operator-console-static/styles.css
  operator-console-static/app.js
  operator-console-static/demo-data/overview-view-model.json
  operator-console-static/demo-data/module-lifecycle-view-model.json
  operator-console-static/demo-data/provider-hardening-view-model.json
  operator-console-static/demo-data/release-readiness-view-model.json
  operator-console-static/demo-data/incidents-view-model.json
  operator-console-static/demo-data/settings-safety-view-model.json
  operator-console-static/demo-data/module-lifecycle-dashboard.json
  operator-console-static/demo-data/generic-knowledge-trail.json
  operator-console-static/demo-data/module-activation-blockers.json
  operator-console-static/demo-data/module-mock-runtime-trail.json
  operator-console-static/demo-data/module-review-checklist.json
  operator-console-static/demo-data/operator-action-preview.json
  operator-console-static/demo-data/operator-action-blockers.json
  operator-console-static/demo-data/operator-action-review.json
  operator-console-static/demo-data/action-authorization-preview.json
  operator-console-static/demo-data/action-authorization-deny-matrix.json
  operator-console-static/demo-data/auth-runtime-status.json
  operator-console-static/demo-data/mock-claims-preview.json
  operator-console-static/demo-data/local-auth-status.json
  operator-console-static/demo-data/role-filtered-view-model.json
  docs/operator-console/static-console-prototype.md
  docs/operator-console/static-console-runbook.md
  docs/operator-console/static-console-safety-review.md
  docs/operator-console/static-console-test-plan.md
  docs/operator-console/module-lifecycle-dashboard.md
  docs/operator-console/generic-knowledge-trail-view.md
  docs/operator-console/module-review-panel.md
  docs/operator-console/module-dashboard-safety-review.md
  docs/operator-console/governed-operator-actions.md
  docs/operator-console/action-preview-panel.md
  docs/operator-console/action-review-flow.md
  docs/operator-console/action-boundary-matrix.md
  docs/adr/0080-static-local-operator-console-prototype.md
  docs/adr/0081-read-only-module-lifecycle-dashboard.md
  docs/adr/0083-governed-operator-actions-dry-run-only.md
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing static console artifact: $file" >&2
    exit 1
  }
done

grep -q "AION Operator Console Prototype — local, read-only, no activation" operator-console-static/index.html || {
  echo "static console banner missing" >&2
  exit 1
}

grep -q "isLocalApiOrigin" operator-console-static/app.js || {
  echo "localhost API guard missing" >&2
  exit 1
}

grep -q "127.0.0.1" operator-console-static/app.js || {
  echo "127.0.0.1 API guard missing" >&2
  exit 1
}

grep -q "apiAllowed: false" operator-console-static/app.js || {
  echo "non-local API block missing" >&2
  exit 1
}

grep -q "/brain/operator-console/view-model" operator-console-static/app.js || {
  echo "view-model endpoint missing" >&2
  exit 1
}

if grep -R -n -E "https?://" operator-console-static | grep -v -E "localhost|127\\.0\\.0\\.1"; then
  echo "non-local URL found in static console" >&2
  exit 1
fi

if grep -n -E "method:[[:space:]]*[\"'](PUT|PATCH|DELETE)[\"']" operator-console-static/app.js; then
  echo "write HTTP method found in app.js" >&2
  exit 1
fi

if grep -n -E "\\b(import|require)[[:space:]]*\\(" operator-console-static/app.js; then
  echo "external library loading found in app.js" >&2
  exit 1
fi

if grep -n "localStorage" operator-console-static/app.js; then
  echo "localStorage usage found in app.js" >&2
  exit 1
fi

if grep -n -E "@import|url\\([[:space:]]*[\"']?https?://" operator-console-static/styles.css; then
  echo "external CSS import found" >&2
  exit 1
fi

for key in raw_prompt hidden_reasoning chain_of_thought password token api_key secret private_key credential authorization bearer; do
  grep -q "$key" operator-console-static/app.js || {
    echo "redaction key missing from app.js: $key" >&2
    exit 1
  }
done

grep -q "0080-static-local-operator-console-prototype.md" docs/adr/README.md || {
  echo "ADR 0080 is not indexed" >&2
  exit 1
}

grep -q "0081-read-only-module-lifecycle-dashboard.md" docs/adr/README.md || {
  echo "ADR 0081 is not indexed" >&2
  exit 1
}

grep -q "0083-governed-operator-actions-dry-run-only.md" docs/adr/README.md || {
  echo "ADR 0083 is not indexed" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
demo_dir = root / "operator-console-static" / "demo-data"
required_actions = {
    "activate_module",
    "activate_capability",
    "load_code",
    "execute_tool",
    "enable_external_model_calls",
    "hard_delete",
}
for path in sorted(demo_dir.glob("*.json")):
    payload = json.loads(path.read_text())
    if path.name.startswith("action-authorization-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"action authorization demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"action authorization demo must be redacted: {path}")
        for key in (
            "write_allowed",
            "execution_allowed",
            "activation_allowed",
            "external_calls_allowed",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"action authorization demo flag must be false: {key}: {path}")
        if payload.get("dry_run_only") is not True:
            raise SystemExit(f"action authorization demo must be dry_run_only: {path}")
        continue
    if path.name.startswith("local-session-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"local session demo must be read_only: {path}")
        for key in (
            "production_session",
            "credential_backed",
            "token_issued",
            "cookie_issued",
            "persistent",
            "write_allowed",
            "execute_allowed",
            "activation_allowed",
            "external_calls_allowed",
        ):
            if payload.get(key) is not False:
                raise SystemExit(f"local session demo flag must be false: {key}: {path}")
        continue
    if path.name.startswith("auth-runtime-") or path.name.startswith("mock-claims-"):
        if payload.get("read_only") is not True:
            raise SystemExit(f"auth runtime demo must be read_only: {path}")
        if payload.get("redaction_applied") is not True:
            raise SystemExit(f"auth runtime demo must be redacted: {path}")
        for key in (
            "production_auth_enabled",
            "auth_runtime_enabled",
            "external_identity_provider_enabled",
            "credentials_enabled",
            "token_issuance_enabled",
            "cookie_issuance_enabled",
            "session_persistence_enabled",
            "login_endpoint_enabled",
            "logout_endpoint_enabled",
            "production_identity",
            "credentials_present",
            "token_present",
            "cookie_present",
            "session_persisted",
            "write_allowed",
            "execute_allowed",
            "activation_allowed",
            "external_calls_allowed",
        ):
            if key in payload and payload.get(key) is not False:
                raise SystemExit(f"auth runtime demo flag must be false: {key}: {path}")
        continue
    if payload.get("read_only") is not True:
        raise SystemExit(f"read_only must be true: {path}")
    if payload.get("redaction_applied") is not True:
        raise SystemExit(f"redaction_applied must be true: {path}")
    for key in ("status", "sections", "blockers", "warnings", "refs"):
        if key not in payload and not any(key in section for section in payload.get("sections", [])):
            raise SystemExit(f"missing {key}: {path}")
    actions = {item.get("action_key") for item in payload.get("forbidden_actions", [])}
    if actions != required_actions:
        raise SystemExit(f"forbidden actions mismatch: {path}")
    serialized = json.dumps(payload, sort_keys=True).lower()
    allowed_authorization_demo_names = {
        "v02-implementation-authorization-preview.json",
        "v02-runtime-enablement-guard-boundary.json",
        "v02-implementation-authorization-stabilization.json",
        "v02-explicit-approval-record-freeze.json",
        "v02-implementation-authorization-final-review.json",
        "v02-runtime-enablement-guard-final-lock.json",
        "v02-authorization-track-closeout.json",
        "v02-runtime-enablement-master-lock.json",
        "v02-production-auth-authorization.json",
        "v02-production-auth-runtime-guard-hold.json",
        "v02-production-auth-core-implementation-closeout.json",
        "v02-production-auth-stabilization-authorization.json",
        "production-auth-core-status.json",
        "production-auth-runtime-hold.json",
        "production-auth-core-stabilization.json",
        "production-auth-core-stabilization-runtime-hold.json",
    }
    blocked = (
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "password",
        "api_key",
        "private_key",
        "authorization",
        "bearer ",
        "sk-",
        "ghp_",
        "xoxb-",
    )
    for value in blocked:
        if value == "authorization" and path.name in allowed_authorization_demo_names:
            continue
        if value == "password" and path.name in {
            "v02-production-auth-authorization.json",
            "v02-production-auth-runtime-guard-hold.json",
            "v02-production-auth-core-implementation-closeout.json",
            "v02-production-auth-stabilization-authorization.json",
            "production-auth-core-status.json",
            "production-auth-runtime-hold.json",
            "production-auth-core-stabilization.json",
            "production-auth-core-stabilization-runtime-hold.json",
        }:
            continue
        if value in serialized:
            raise SystemExit(f"unsafe demo content: {path}")

changed = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
blocked_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
blocked_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
    "webpack.config.",
)
for name in [*changed, *untracked]:
    basename = Path(name).name
    if basename in blocked_names or any(basename.startswith(prefix) for prefix in blocked_prefixes):
        raise SystemExit(f"frontend package or build file changed: {name}")

print("Static console JSON and artifact checks PASS")
PY

echo "Operator console static check PASS"
