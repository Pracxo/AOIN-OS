#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  operator-console-static/README.md
  operator-console-static/index.html
  operator-console-static/styles.css
  operator-console-static/app.js
)

for file in "${required_files[@]}"; do
  test -f "$file" || {
    echo "missing static console file: $file" >&2
    exit 1
  }
done

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

for banner in \
  "read-only" \
  "no activation" \
  "no execution" \
  "no provider calls" \
  "no login" \
  "no credentials" \
  "UI Release Gate: read-only, local, dependency-free"; do
  grep -i -q "$banner" operator-console-static/index.html || {
    echo "static console banner missing: $banner" >&2
    exit 1
  }
done

if rg -n '<script[^>]+src=["'\''](https?:)?//' operator-console-static/index.html; then
  echo "external script tag found" >&2
  exit 1
fi

if rg -n '@import|url\([[:space:]]*["'\'']?https?://' operator-console-static/styles.css; then
  echo "external CSS import found" >&2
  exit 1
fi

if rg -n 'https?://' operator-console-static | rg -v 'localhost|127\.0\.0\.1'; then
  echo "non-local URL found in static console" >&2
  exit 1
fi

if rg -n '<form|<input|type=["'\'']password|name=["'\'']?(password|token|cookie|credential)' \
  operator-console-static/index.html; then
  echo "login, password, token, cookie, or credential input found" >&2
  exit 1
fi

if rg -n 'localStorage|sessionStorage' operator-console-static/app.js; then
  echo "browser storage usage found" >&2
  exit 1
fi

if rg -n 'method:[[:space:]]*["'\''](PUT|PATCH|DELETE)["'\'']' operator-console-static/app.js; then
  echo "write HTTP method found in app.js" >&2
  exit 1
fi

for key in raw_prompt hidden_reasoning secret credential token authorization bearer; do
  grep -q "$key" operator-console-static/app.js || {
    echo "redaction key missing from app.js: $key" >&2
    exit 1
  }
done

grep -q "loadDemo" operator-console-static/app.js || {
  echo "demo fallback loader missing" >&2
  exit 1
}

grep -q "demo-data" operator-console-static/app.js || {
  echo "demo-data fallback references missing" >&2
  exit 1
}

if rg -n 'production ready|production-ready|ready for production' operator-console-static; then
  echo "production-ready UI claim found" >&2
  exit 1
fi

if rg -n 'npm[[:space:]]+install|pnpm[[:space:]]+install|yarn[[:space:]]+add|bun[[:space:]]+add' \
  operator-console-static; then
  echo "package install instruction found in static console" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
static_dir = root / "operator-console-static"
html = (static_dir / "index.html").read_text()
app = (static_dir / "app.js").read_text()

if "isLocalApiOrigin" not in app or "apiAllowed: false" not in app:
    raise SystemExit("localhost API guard missing")
if 'parsed.hostname === "localhost"' not in app:
    raise SystemExit("localhost origin check missing")
if 'parsed.hostname === "127.0.0.1"' not in app:
    raise SystemExit("127.0.0.1 origin check missing")

button_pattern = re.compile(r"<button\b(?P<attrs>[^>]*)>(?P<body>.*?)</button>", re.I | re.S)
danger_words = (
    "activate",
    "execute",
    "call provider",
    "provider call",
    "login",
    "logout",
    "credential",
    "token",
    "cookie",
)
safe_negative = (
    "actions disabled",
    "activation blocked",
    "demo only",
    "no ",
    "preview only",
)
for match in button_pattern.finditer(html):
    attrs = match.group("attrs").lower()
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group("body"))).strip().lower()
    if any(word in text for word in danger_words):
        if "disabled" not in attrs:
            raise SystemExit(f"dangerous enabled button found: {text}")
        if not text.startswith(safe_negative):
            raise SystemExit(f"dangerous button label is not a no-go label: {text}")

false_flags = {
    "activation_allowed",
    "auth_runtime_enabled",
    "cookie_issuance_enabled",
    "credentials_enabled",
    "execution_allowed",
    "external_calls_allowed",
    "production_auth_enabled",
    "session_persistence_enabled",
    "token_issuance_enabled",
}
unsafe_markers = (
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
    "v02-production-auth-request-boundary-authorization.json",
    "v02-production-auth-request-identity-stabilization-authorization.json",
    "v02-actor-context-trust-boundary-authorization.json",
    "v02-offline-identity-assertion-verification-authorization.json",
    "v02-identity-assertion-replay-protection-authorization.json",
    "self-improvement-shadow-mode-authorization.json",
    "self-improvement-shadow-mode-operator-evaluation.json",
    "self-improvement-shadow-mode-activation-review-boundary.json",
    "self-improvement-actual-shadow-activation-review-boundary.json",
    "self-improvement-shadow-activation-authorization.json",
    "self-improvement-shadow-activation-runtime-hold.json",
    "self-improvement-shadow-activation-control-plane-evaluation.json",
    "production-auth-core-status.json",
    "production-auth-runtime-hold.json",
    "production-auth-core-stabilization.json",
    "production-auth-core-stabilization-runtime-hold.json",
    "production-auth-request-identity-boundary.json",
    "production-auth-request-identity-runtime-hold.json",
    "production-auth-request-identity-stabilization.json",
    "production-auth-request-identity-stabilization-runtime-hold.json",
    "actor-context-trust-boundary.json",
    "actor-context-runtime-hold.json",
    "knowledge-intelligence-program.json",
    "knowledge-intelligence-research-authorization.json",
    "knowledge-intelligence-research-plane.json",
    "knowledge-intelligence-research-runtime-hold.json",
    "knowledge-intelligence-source-lineage.json",
    "knowledge-intelligence-source-snapshots.json",
    "knowledge-intelligence-research-evaluation.json",
    "knowledge-intelligence-source-registry-authorization.json",
    "knowledge-intelligence-source-registry.json",
    "knowledge-intelligence-source-registry-index.json",
    "knowledge-intelligence-source-registry-integrity.json",
    "knowledge-intelligence-source-registry-runtime-hold.json",
    "knowledge-intelligence-source-registry-evaluation.json",
    "knowledge-intelligence-claim-graph-authorization.json",
    "knowledge-intelligence-claim-graph-evaluation.json",
    "knowledge-intelligence-claim-graph-runtime-hold.json",
    "knowledge-intelligence-epistemic-assessment.json",
    "knowledge-intelligence-epistemic-hard-caps.json",
    "knowledge-intelligence-epistemic-integrity.json",
    "knowledge-intelligence-epistemic-runtime-hold.json",
    "knowledge-intelligence-epistemic-scorecard.json",
    "knowledge-intelligence-epistemic-truth-authorization.json",
    "knowledge-intelligence-epistemic-assessment-evaluation.json",
    "knowledge-intelligence-domain-expert-mesh-authorization.json",
    "knowledge-intelligence-domain-expert-mesh-evaluation.json",
    "knowledge-intelligence-domain-expert-mesh-budget.json",
    "knowledge-intelligence-domain-expert-mesh-disagreement.json",
    "knowledge-intelligence-domain-expert-mesh-panel-policy.json",
    "knowledge-intelligence-integrated-research-agent-evaluation.json",
    "knowledge-intelligence-verified-knowledge-authorization.json",
    "knowledge-intelligence-domain-expert-mesh-panel.json",
    "knowledge-intelligence-domain-expert-mesh-runtime-hold.json",
    "knowledge-intelligence-domain-expert-critiques.json",
    "knowledge-intelligence-domain-expert-disagreement.json",
    "knowledge-intelligence-domain-expert-integrity.json",
    "knowledge-intelligence-domain-expert-mesh.json",
    "knowledge-intelligence-domain-expert-panel.json",
    "knowledge-intelligence-domain-expert-reports.json",
    "knowledge-intelligence-domain-expert-runtime-hold.json",
    "knowledge-intelligence-domain-expert-synthesis.json",
    "knowledge-intelligence-tool-attestation.json",
    "knowledge-intelligence-tool-manifest.json",
    "knowledge-intelligence-tool-plan.json",
    "knowledge-intelligence-tool-simulation.json",
    "knowledge-intelligence-tool-verification-authorization.json",
    "knowledge-intelligence-tool-verification-runtime-hold.json",
    "knowledge-intelligence-verified-memory-evaluation.json",
    "knowledge-intelligence-public-research-pilot-authorization.json",
    "knowledge-intelligence-public-research-pilot-integrity.json",
    "knowledge-intelligence-public-research-pilot-live-evidence.json",
    "knowledge-intelligence-public-research-pilot-network-policy.json",
    "knowledge-intelligence-public-research-pilot-resource-budget.json",
    "knowledge-intelligence-public-research-pilot-result.json",
    "knowledge-intelligence-public-research-pilot-runtime-hold.json",
    "governed-learning-memory-authorization.json",
    "governed-learning-memory-boundary.json",
    "governed-learning-memory-program.json",
    "governed-learning-memory-promotion-request.json",
    "governed-learning-memory-approval-evidence.json",
    "governed-learning-memory-eligibility.json",
    "governed-learning-memory-knowledge-identity.json",
    "governed-learning-memory-conflicts.json",
    "governed-learning-memory-version-plan.json",
    "governed-learning-memory-projection-plan.json",
    "governed-learning-memory-transaction-result.json",
    "governed-learning-memory-integrity.json",
    "governed-learning-memory-engagement-application-authorization.json",
    "governed-learning-memory-engagement-evaluation.json",
    "governed-learning-memory-continual-learning-authorization.json",
    "governed-learning-memory-continual-learning-authorization-envelope.json",
    "governed-learning-memory-continual-learning-candidate-binding.json",
    "governed-learning-memory-continual-learning-cross-cycle-context.json",
    "governed-learning-memory-continual-learning-cycle.json",
    "governed-learning-memory-continual-learning-cycle-outcomes.json",
    "governed-learning-memory-continual-learning-cycle-plans.json",
    "governed-learning-memory-continual-learning-evidence-bundle.json",
    "governed-learning-memory-continual-learning-integrity-report.json",
    "governed-learning-memory-continual-learning-live-pilot-evidence.json",
    "governed-learning-memory-continual-learning-outcome.json",
    "governed-learning-memory-continual-learning-persistence-binding.json",
    "governed-learning-memory-continual-learning-persistence.json",
    "governed-learning-memory-continual-learning-promotion-binding.json",
    "governed-learning-memory-continual-learning-research-binding.json",
    "governed-learning-memory-continual-learning-research.json",
    "governed-learning-memory-continual-learning-runtime-boundary.json",
    "governed-learning-memory-continual-learning-runtime-hold.json",
    "governed-learning-memory-continual-learning-session-plan.json",
    "governed-learning-memory-continual-learning-session-result.json",
    "governed-learning-memory-continual-learning-shadow-binding.json",
    "governed-learning-memory-continual-learning-shadow.json",
    "governed-learning-memory-continual-learning-stage-command.json",
    "governed-learning-memory-continual-learning-stage-receipt.json",
    "governed-learning-memory-engagement-adaptation-identity.json",
    "governed-learning-memory-engagement-application-plan.json",
    "governed-learning-memory-engagement-application-result.json",
    "governed-learning-memory-engagement-approval-bundle.json",
    "governed-learning-memory-engagement-authorization.json",
    "governed-learning-memory-engagement-baseline-snapshot.json",
    "governed-learning-memory-engagement-candidate-binding.json",
    "governed-learning-memory-engagement-conflict-report.json",
    "governed-learning-memory-engagement-counterfactual-result.json",
    "governed-learning-memory-engagement-counterfactual.json",
    "governed-learning-memory-engagement-integrity-report.json",
    "governed-learning-memory-engagement-integrity.json",
    "governed-learning-memory-engagement-lifecycle-evidence.json",
    "governed-learning-memory-engagement-metric-delta.json",
    "governed-learning-memory-engagement-overlay-record.json",
    "governed-learning-memory-engagement-overlay-snapshot.json",
    "governed-learning-memory-engagement-overlay.json",
    "governed-learning-memory-engagement-risk-assessment.json",
    "governed-learning-memory-engagement-risk-policy.json",
    "governed-learning-memory-engagement-rollback-plan.json",
    "governed-learning-memory-engagement-runtime-boundary.json",
    "governed-learning-memory-engagement-runtime-hold.json",
    "governed-learning-memory-engagement-synthetic-pilot.json",
    "governed-learning-memory-engagement-target-policy.json",
    "governed-learning-memory-engagement-version-plan.json",
    "governed-learning-memory-local-persistence-approval.json",
    "governed-learning-memory-local-persistence-authorization.json",
    "governed-learning-memory-local-persistence-evaluation.json",
    "governed-learning-memory-local-persistence-integrity.json",
    "governed-learning-memory-local-persistence-projection.json",
    "governed-learning-memory-local-persistence-runtime-hold.json",
    "governed-learning-memory-local-persistence-schema.json",
    "governed-learning-memory-local-persistence-version.json",
    "governed-learning-memory-promotion-evaluation.json",
    "governed-learning-memory-roadmap.json",
    "governed-learning-memory-runtime-hold.json",
}
aion161_allowed_policy_markers = {
    "runtime_private_key",
    "private_key_configuration",
    "private_key_persistence",
    "private_key_serialization",
}


def walk(value: object, path: Path) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in false_flags and nested is not False:
                raise SystemExit(f"{normalized} must be false in {path}")
            walk(nested, path)
    elif isinstance(value, list):
        for item in value:
            walk(item, path)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in unsafe_markers:
            if (
                marker == "raw_prompt"
                and path.name == "knowledge-intelligence-tool-manifest.json"
                and lowered == "raw_prompt"
            ):
                continue
            if marker == "authorization" and path.name in allowed_authorization_demo_names:
                continue
            if marker == "sk-" and not re.search(r"\bsk-[a-z0-9_-]{12,}", lowered):
                continue
            if (
                marker == "private_key"
                and path.name
                in {
                    "v02-offline-identity-assertion-verification-authorization.json",
                    "v02-identity-assertion-replay-protection-authorization.json",
                }
                and lowered in aion161_allowed_policy_markers
            ):
                continue
            if marker == "password" and path.name in {
                "v02-production-auth-authorization.json",
                "v02-production-auth-runtime-guard-hold.json",
                "v02-production-auth-core-implementation-closeout.json",
                "v02-production-auth-stabilization-authorization.json",
                "v02-production-auth-request-boundary-authorization.json",
                "v02-production-auth-request-identity-stabilization-authorization.json",
                "v02-actor-context-trust-boundary-authorization.json",
                "production-auth-core-status.json",
                "production-auth-runtime-hold.json",
                "production-auth-core-stabilization.json",
                "production-auth-core-stabilization-runtime-hold.json",
                "production-auth-request-identity-boundary.json",
                "production-auth-request-identity-runtime-hold.json",
                "production-auth-request-identity-stabilization.json",
                "production-auth-request-identity-stabilization-runtime-hold.json",
                "actor-context-trust-boundary.json",
                "actor-context-runtime-hold.json",
            }:
                continue
            if marker in lowered:
                raise SystemExit(f"unsafe demo content in {path}")


for path in sorted((static_dir / "demo-data").glob("*.json")):
    payload = json.loads(path.read_text())
    walk(payload, path)

print("Static console safety JSON checks PASS")
PY

echo "Static console safety check PASS"
