#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/auth/production-auth-architecture.md
  docs/auth/auth-provider-evaluation-matrix.md
  docs/auth/identity-provider-boundary-model.md
  docs/auth/token-session-storage-decision.md
  docs/auth/credential-handling-no-go-rules.md
  docs/auth/production-auth-threat-model.md
  docs/auth/production-auth-release-gates.md
  docs/auth/disabled-auth-prototype-plan.md
  docs/adr/0089-production-auth-architecture-decision.md
)

required_examples=(
  examples/auth/production-auth-provider-matrix.json
  examples/auth/production-auth-threat-model.json
  examples/auth/disabled-auth-prototype-plan.json
  examples/auth/production-auth-release-gates.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || { echo "missing production auth doc: $file" >&2; exit 1; }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || { echo "missing production auth example: $file" >&2; exit 1; }
done

grep -q "0089-production-auth-architecture-decision.md" docs/adr/README.md || {
  echo "ADR 0089 is not indexed" >&2
  exit 1
}

grep -R -q "No production auth is implemented in AION-098" \
  docs/auth/production-auth-architecture.md \
  docs/adr/0089-production-auth-architecture-decision.md || {
  echo "docs must state no production auth implementation in AION-098" >&2
  exit 1
}

grep -R -q "production_auth_enabled.*remains false" docs/auth docs/adr/0089-production-auth-architecture-decision.md || {
  echo "docs must state production_auth_enabled remains false" >&2
  exit 1
}

grep -R -q "No provider integration is added in AION-098" docs/auth/production-auth-architecture.md || {
  echo "docs must state no provider integration in AION-098" >&2
  exit 1
}

grep -q "No credentials, tokens, sessions," docs/auth/production-auth-architecture.md && \
grep -q "or cookies are created, stored, issued, or accepted" docs/auth/production-auth-architecture.md || {
  echo "docs must state no credentials/tokens/sessions/cookies" >&2
  exit 1
}

if rg -n '@router\.(get|post|put|patch|delete)\([^)]*(login|logout)' services/brain-api/src/aion_brain/api; then
  echo "login/logout endpoint string found in API routes" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- infra/postgres/migrations | rg -n '098|auth|session|token|cookie'; then
  echo "AION-098 must not add a migration" >&2
  exit 1
fi

if git ls-files --others --exclude-standard | rg -n '^infra/postgres/migrations/.*(098|auth|session|token|cookie)'; then
  echo "AION-098 must not add an untracked migration" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- . | rg -n '(^|/)(package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb)$'; then
  echo "package file changed" >&2
  exit 1
fi

if git ls-files --others --exclude-standard | rg -n '(^|/)(package.json|package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb)$'; then
  echo "package file added" >&2
  exit 1
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- pyproject.toml services packages requirements.txt setup.cfg setup.py | rg -n '.' >/dev/null; then
  if git diff HEAD -- pyproject.toml services packages requirements.txt setup.cfg setup.py \
    | rg -n 'authlib|oauth|oidc|saml|ldap|webauthn|passkey|python-jose|jwt|okta|auth0' \
    | rg -v 'production_auth_(oauth|oidc|saml)_runtime_enabled|AION_PRODUCTION_AUTH_(OAUTH|OIDC|SAML)_RUNTIME_ENABLED|(oauth|oidc|saml)_runtime_enabled'; then
    echo "runtime auth provider SDK dependency found" >&2
    exit 1
  fi
fi

if git diff --name-only --diff-filter=ACMRT HEAD -- services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/auth_runtime.py$' \
  | rg -n 'auth|login|logout|session|token|cookie'; then
  echo "AION-098 must not change auth runtime API routes" >&2
  exit 1
fi

if git ls-files --others --exclude-standard services/brain-api/src/aion_brain/api \
  | rg -v '^services/brain-api/src/aion_brain/api/auth_runtime.py$' \
  | rg -n 'auth|login|logout|session|token|cookie'; then
  echo "AION-098 must not add auth runtime API routes" >&2
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
examples = [
    root / "examples/auth/production-auth-provider-matrix.json",
    root / "examples/auth/production-auth-threat-model.json",
    root / "examples/auth/disabled-auth-prototype-plan.json",
    root / "examples/auth/production-auth-release-gates.json",
]
secret_markers = (
    "sk-",
    "ghp_",
    "xoxb-",
    "-----begin private key-----",
    "bearer ",
    "basic ",
    "client_secret",
    "private_key",
)
real_value_keys = {
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "cookie",
    "session_id",
    "session_token",
    "password",
    "api_key",
    "client_secret",
    "provider_endpoint",
}


def walk(value: object, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered_key = str(key).lower()
            if lowered_key in real_value_keys and nested not in (False, None, "", [], {}):
                if not (lowered_key == "provider_endpoint" and nested is False):
                    raise SystemExit(f"real auth material in {'.'.join((*path, str(key)))}")
            walk(nested, (*path, str(key)))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            walk(nested, (*path, str(index)))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in secret_markers):
            raise SystemExit(f"secret-like marker in {'.'.join(path)}")
        if "http://" in lowered or "https://" in lowered:
            raise SystemExit(f"provider endpoint-like value in {'.'.join(path)}")


for path in examples:
    payload = json.loads(path.read_text())
    if payload.get("synthetic") is not True:
        raise SystemExit(f"example must be synthetic: {path}")
    walk(payload, (path.name,))

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

runtime_prefixes = (
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/contracts/",
    "services/brain-api/src/aion_brain/local_auth/",
    "services/brain-api/src/aion_brain/local_session/",
    "services/brain-api/src/aion_brain/action_authorization/",
    "packages/aion-sdk-python/src/aion_sdk/resources/",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/",
)
allowed_runtime_tests = (
    "services/brain-api/tests/test_production_auth_architecture_docs.py",
)
allowed_aion_099_runtime = {
    "services/brain-api/src/aion_brain/api/auth_runtime.py",
    "services/brain-api/src/aion_brain/contracts/auth_runtime.py",
    "services/brain-api/src/aion_brain/contracts/telemetry.py",
    "services/brain-api/src/aion_brain/local_auth/audit.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/auth_runtime.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/auth_runtime.py",
    "packages/aion-sdk-python/tests/test_auth_runtime_resource.py",
    "packages/aion-sdk-python/tests/test_cli_auth_runtime.py",
    "services/brain-api/tests/test_auth_runtime_contracts.py",
    "services/brain-api/tests/test_auth_runtime_redaction.py",
    "services/brain-api/tests/test_auth_runtime_services.py",
    "services/brain-api/tests/test_auth_runtime_audit.py",
    "services/brain-api/tests/test_auth_runtime_api.py",
    "services/brain-api/tests/test_kernel_auth_runtime_wiring.py",
    "services/brain-api/tests/test_visual_telemetry_auth_runtime.py",
}
allowed_aion_108_runtime = {
    "services/brain-api/src/aion_brain/api/connector_runtime.py",
    "services/brain-api/src/aion_brain/contracts/connector_runtime.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_runtime.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_runtime.py",
}
allowed_aion_110_runtime = {
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "services/brain-api/src/aion_brain/contracts/connector_simulator.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator.py",
}
allowed_aion_111_runtime = {
    "services/brain-api/src/aion_brain/api/connector_policy.py",
    "services/brain-api/src/aion_brain/contracts/connector_policy.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_policy.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_policy.py",
}
allowed_aion_112_runtime = {
    "services/brain-api/src/aion_brain/api/connector_sandbox.py",
    "services/brain-api/src/aion_brain/contracts/connector_sandbox.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_sandbox.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_sandbox.py",
}
allowed_aion_113_runtime = {
    "services/brain-api/src/aion_brain/api/connector_credentials.py",
    "services/brain-api/src/aion_brain/contracts/connector_credentials.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_credentials.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_credentials.py",
}
allowed_aion_152_runtime = {
    "services/brain-api/src/aion_brain/contracts/production_auth.py",
    "services/brain-api/src/aion_brain/local_auth/audit.py",
}
allowed_aion_156_runtime = {
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/request_boundary.py",
    "services/brain-api/src/aion_brain/production_auth/request_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/request_middleware.py",
    "services/brain-api/src/aion_brain/production_auth/verifier.py",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel/app_factory.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
}
allowed_aion_160_runtime = {
    "services/brain-api/src/aion_brain/contracts/actor_context_resolution.py",
}
allowed_aion_162_runtime = {
    "services/brain-api/src/aion_brain/contracts/identity_assertion.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py",
    "services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py",
}
allowed_aion_164_runtime = {
    "services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py",
}
allowed_aion_166_runtime = {
    "services/brain-api/src/aion_brain/contracts/self_improvement.py",
    "services/brain-api/src/aion_brain/self_improvement/__init__.py",
    "services/brain-api/src/aion_brain/self_improvement/approval.py",
    "services/brain-api/src/aion_brain/self_improvement/change_budget.py",
    "services/brain-api/src/aion_brain/self_improvement/evidence.py",
    "services/brain-api/src/aion_brain/self_improvement/governance.py",
    "services/brain-api/src/aion_brain/self_improvement/ledger.py",
    "services/brain-api/src/aion_brain/self_improvement/lifecycle.py",
    "services/brain-api/src/aion_brain/self_improvement/protected_paths.py",
    "services/brain-api/src/aion_brain/self_improvement/risk.py",
}
allowed_aion_168_runtime = {
    "services/brain-api/src/aion_brain/self_improvement/__init__.py",
    "services/brain-api/src/aion_brain/self_improvement/benchmark_contracts.py",
    "services/brain-api/src/aion_brain/self_improvement/benchmark_registry.py",
    "services/brain-api/src/aion_brain/self_improvement/benchmark_runner.py",
    "services/brain-api/src/aion_brain/self_improvement/comparison.py",
    "services/brain-api/src/aion_brain/self_improvement/evaluation_evidence.py",
    "services/brain-api/src/aion_brain/self_improvement/holdout.py",
    "services/brain-api/src/aion_brain/self_improvement/scoring.py",
}
allowed_aion_178_runtime = {
    "services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_budget.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_observation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_runner.py",
}
for name in [*changed, *untracked]:
    if name in allowed_runtime_tests:
        continue
    if name in allowed_aion_099_runtime:
        continue
    if name in allowed_aion_108_runtime:
        continue
    if name in allowed_aion_110_runtime:
        continue
    if name in allowed_aion_111_runtime:
        continue
    if name in allowed_aion_112_runtime:
        continue
    if name in allowed_aion_113_runtime:
        continue
    if name in allowed_aion_152_runtime:
        continue
    if name in allowed_aion_156_runtime:
        continue
    if name in allowed_aion_160_runtime:
        continue
    if name in allowed_aion_162_runtime:
        continue
    if name in allowed_aion_164_runtime:
        continue
    if name in allowed_aion_166_runtime:
        continue
    if name in allowed_aion_168_runtime:
        continue
    if name in allowed_aion_178_runtime:
        continue
    if name.startswith(runtime_prefixes):
        raise SystemExit(f"production auth architecture must not change runtime file: {name}")

print("Production auth architecture examples valid")
PY

echo "Production auth architecture check PASS"
