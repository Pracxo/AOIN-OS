#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

required_docs=(
  docs/auth/local-auth-design.md
  docs/auth/local-auth-contract.md
  docs/auth/dev-identity-simulation.md
  docs/auth/role-aware-console-filtering.md
  docs/auth/local-auth-audit.md
  docs/auth/local-auth-runtime-boundaries.md
  docs/auth/operator-identity-model.md
  docs/auth/operator-session-boundary.md
  docs/auth/operator-role-model.md
  docs/auth/operator-access-matrix.md
  docs/auth/operator-auth-threat-model.md
  docs/auth/production-auth-prerequisites.md
  docs/auth/auth-no-go-conditions.md
  docs/auth/future-auth-implementation-plan.md
  docs/auth/role-permission-proof-matrix.md
  docs/auth/console-view-access-filtering.md
  docs/auth/role-aware-action-descriptors.md
  docs/auth/role-access-audit.md
  docs/auth/dry-run-action-permission-model.md
  docs/auth/action-authorization-audit.md
  docs/auth/production-auth-architecture.md
  docs/auth/auth-provider-evaluation-matrix.md
  docs/auth/identity-provider-boundary-model.md
  docs/auth/token-session-storage-decision.md
  docs/auth/credential-handling-no-go-rules.md
  docs/auth/production-auth-threat-model.md
  docs/auth/production-auth-release-gates.md
  docs/auth/disabled-auth-prototype-plan.md
  docs/adr/0084-local-auth-design-for-operator-console.md
  docs/adr/0085-local-auth-contract-dev-identity-simulation.md
  docs/adr/0087-role-aware-console-view-filtering.md
  docs/adr/0088-dry-run-action-authorization-enforcement.md
  docs/adr/0089-production-auth-architecture-decision.md
)

required_examples=(
  examples/auth/local-operator-identity.json
  examples/auth/operator-role-matrix.json
  examples/auth/session-boundary-example.json
  examples/auth/console-access-policy-example.json
  examples/auth/local-auth-status.json
  examples/auth/dev-identity-simulation-request.json
  examples/auth/role-filtered-viewer-console.json
  examples/auth/role-filtered-operator-console.json
  examples/auth/local-auth-audit-request.json
  examples/auth/role-permission-proof-matrix.json
  examples/auth/viewer-access-filter-result.json
  examples/auth/operator-access-filter-result.json
  examples/auth/reviewer-access-filter-result.json
  examples/auth/auditor-access-filter-result.json
  examples/auth/admin-access-filter-result.json
  examples/auth/role-access-audit-result.json
  examples/auth/dry-run-action-authorization-request.json
  examples/auth/dry-run-action-authorization-decision.json
  examples/auth/action-authorization-deny-examples.json
  examples/auth/action-authorization-audit-result.json
  examples/auth/production-auth-provider-matrix.json
  examples/auth/production-auth-threat-model.json
  examples/auth/disabled-auth-prototype-plan.json
  examples/auth/production-auth-release-gates.json
)

for file in "${required_docs[@]}"; do
  test -f "$file" || { echo "missing auth doc: $file" >&2; exit 1; }
done

for file in "${required_examples[@]}"; do
  test -f "$file" || { echo "missing auth example: $file" >&2; exit 1; }
done

grep -q "0084-local-auth-design-for-operator-console.md" docs/adr/README.md || {
  echo "ADR 0084 is not indexed" >&2
  exit 1
}

grep -q "0085-local-auth-contract-dev-identity-simulation.md" docs/adr/README.md || {
  echo "ADR 0085 is not indexed" >&2
  exit 1
}

grep -q "docs/auth/local-auth-design.md" README.md || {
  echo "README missing local auth design link" >&2
  exit 1
}

grep -q "Do not implement production auth" AGENTS.md || {
  echo "AGENTS missing auth guardrails" >&2
  exit 1
}

grep -R -q "no production auth is implemented" docs/auth README.md || {
  echo "docs must state no production auth is implemented" >&2
  exit 1
}

grep -R -q "No credentials are stored" docs/auth README.md || {
  echo "docs must state no credentials are stored" >&2
  exit 1
}

grep -R -q "No login endpoint is added" docs/auth README.md || {
  echo "docs must state no login endpoint is added" >&2
  exit 1
}

grep -R -q "No external identity provider is integrated" docs/auth README.md || {
  echo "docs must state no external identity provider is integrated" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
aion_104_review_examples = {
    "auth-safety-evidence-pack.json",
    "auth-runtime-disabled-proof.json",
    "auth-traceability-matrix.json",
    "auth-no-go-regression-result.json",
}
for path in sorted((root / "examples" / "auth").glob("*.json")):
    if path.name in aion_104_review_examples:
        continue
    if path.name.startswith("local-session") or path.name == "role-aware-session-context.json":
        continue
    if "authorization" in path.name:
        continue
    if "auth-runtime" in path.name or "mock-claims" in path.name:
        continue
    if "production-auth" in path.name or path.name == "disabled-auth-prototype-plan.json":
        continue
    payload = json.loads(path.read_text())
    serialized = json.dumps(payload, sort_keys=True).lower()
    blocked = (
        "token",
        "password",
        "secret",
        "api_key",
        "private_key",
        "authorization",
        "bearer",
        "sk-",
        "ghp_",
        "xoxb-",
    )
    if any(item in serialized for item in blocked):
        raise SystemExit(f"auth example contains blocked material: {path}")

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

allowed_auth_paths = {
    "docs/auth/local-auth-design.md",
    "docs/auth/local-auth-contract.md",
    "docs/auth/dev-identity-simulation.md",
    "docs/auth/role-aware-console-filtering.md",
    "docs/auth/local-auth-audit.md",
    "docs/auth/local-auth-runtime-boundaries.md",
    "docs/auth/operator-identity-model.md",
    "docs/auth/operator-session-boundary.md",
    "docs/auth/operator-role-model.md",
    "docs/auth/operator-access-matrix.md",
    "docs/auth/operator-auth-threat-model.md",
    "docs/auth/production-auth-prerequisites.md",
    "docs/auth/auth-no-go-conditions.md",
    "docs/auth/future-auth-implementation-plan.md",
    "docs/auth/role-permission-proof-matrix.md",
    "docs/auth/console-view-access-filtering.md",
    "docs/auth/role-aware-action-descriptors.md",
    "docs/auth/role-access-audit.md",
    "docs/auth/dry-run-action-permission-model.md",
    "docs/auth/action-authorization-audit.md",
    "docs/auth/production-auth-architecture.md",
    "docs/auth/auth-provider-evaluation-matrix.md",
    "docs/auth/identity-provider-boundary-model.md",
    "docs/auth/token-session-storage-decision.md",
    "docs/auth/credential-handling-no-go-rules.md",
    "docs/auth/production-auth-threat-model.md",
    "docs/auth/production-auth-release-gates.md",
    "docs/auth/disabled-auth-prototype-plan.md",
    "docs/auth/disabled-production-auth-prototype.md",
    "docs/auth/mock-claims-adapter.md",
    "docs/auth/auth-runtime-gate.md",
    "docs/auth/auth-runtime-audit.md",
    "docs/auth/auth-runtime-no-go.md",
    "docs/auth/local-auth-prototype-review.md",
    "docs/auth/auth-safety-evidence-pack.md",
    "docs/auth/auth-runtime-disabled-proof.md",
    "docs/auth/auth-traceability-matrix.md",
    "docs/auth/auth-no-go-regression-pack.md",
    "docs/auth/pre-implementation-auth-gate.md",
    "docs/adr/0138-v02-implementation-authorization-preview.md",
    "docs/release/v02-authorization-evidence-matrix.md",
    "docs/release/v02-authorization-state-model.md",
    "docs/release/v02-implementation-authorization-checklist.md",
    "docs/release/v02-implementation-authorization-no-go.md",
    "docs/release/v02-implementation-authorization-preview.md",
    "docs/connectors/connector-authorization-matrix.md",
    "docs/connectors/connector-credential-authorization-matrix.md",
    "docs/operator-console/dry-run-action-authorization.md",
    "docs/operator-console/action-authorization-preview.md",
    "docs/operator-console/action-authorization-deny-matrix.md",
    "docs/adr/0084-local-auth-design-for-operator-console.md",
    "docs/adr/0085-local-auth-contract-dev-identity-simulation.md",
    "docs/adr/0088-dry-run-action-authorization-enforcement.md",
    "docs/adr/0089-production-auth-architecture-decision.md",
    "docs/adr/0090-disabled-production-auth-prototype.md",
    "docs/adr/0095-local-auth-prototype-review-gate.md",
    "examples/auth/local-operator-identity.json",
    "examples/auth/operator-role-matrix.json",
    "examples/auth/session-boundary-example.json",
    "examples/auth/console-access-policy-example.json",
    "examples/auth/local-auth-status.json",
    "examples/auth/dev-identity-simulation-request.json",
    "examples/auth/role-filtered-viewer-console.json",
    "examples/auth/role-filtered-operator-console.json",
    "examples/auth/local-auth-audit-request.json",
    "examples/auth/role-permission-proof-matrix.json",
    "examples/auth/viewer-access-filter-result.json",
    "examples/auth/operator-access-filter-result.json",
    "examples/auth/reviewer-access-filter-result.json",
    "examples/auth/auditor-access-filter-result.json",
    "examples/auth/admin-access-filter-result.json",
    "examples/auth/role-access-audit-result.json",
    "examples/auth/dry-run-action-authorization-request.json",
    "examples/auth/dry-run-action-authorization-decision.json",
    "examples/auth/action-authorization-deny-examples.json",
    "examples/auth/action-authorization-audit-result.json",
    "examples/auth/production-auth-provider-matrix.json",
    "examples/auth/production-auth-threat-model.json",
    "examples/auth/disabled-auth-prototype-plan.json",
    "examples/auth/production-auth-release-gates.json",
    "examples/auth/auth-runtime-status.json",
    "examples/auth/mock-claims-preview-request.json",
    "examples/auth/mock-claims-preview-result.json",
    "examples/auth/auth-runtime-audit-request.json",
    "examples/auth/auth-runtime-blockers.json",
    "examples/auth/auth-safety-evidence-pack.json",
    "examples/auth/auth-runtime-disabled-proof.json",
    "examples/auth/auth-traceability-matrix.json",
    "examples/auth/auth-no-go-regression-result.json",
    "examples/release/v02-authorization-evidence-matrix.json",
    "examples/release/v02-authorization-state-model.json",
    "examples/release/v02-implementation-authorization-preview.json",
    "examples/connectors/connector-authorization-matrix.json",
    "examples/connectors/connector-credential-authorization-matrix.json",
    "operator-console-static/demo-data/v02-implementation-authorization-preview.json",
    "operator-console-static/demo-data/action-authorization-preview.json",
    "operator-console-static/demo-data/action-authorization-deny-matrix.json",
    "operator-console-static/demo-data/auth-runtime-status.json",
    "operator-console-static/demo-data/mock-claims-preview.json",
    "scripts/action-authorization-check.sh",
    "scripts/production-auth-architecture-check.sh",
    "scripts/auth-runtime-check.sh",
    "services/brain-api/src/aion_brain/contracts/action_authorization.py",
    "services/brain-api/src/aion_brain/action_authorization/__init__.py",
    "services/brain-api/src/aion_brain/action_authorization/redaction.py",
    "services/brain-api/src/aion_brain/action_authorization/policy.py",
    "services/brain-api/src/aion_brain/action_authorization/decisions.py",
    "services/brain-api/src/aion_brain/action_authorization/evaluator.py",
    "services/brain-api/src/aion_brain/action_authorization/blockers.py",
    "services/brain-api/src/aion_brain/action_authorization/audit.py",
    "services/brain-api/src/aion_brain/action_authorization/query.py",
    "services/brain-api/src/aion_brain/api/action_authorization.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/action_authorization.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/action_authorization.py",
    "packages/aion-sdk-python/tests/test_action_authorization_resource.py",
    "packages/aion-sdk-python/tests/test_cli_action_authorization.py",
    "services/brain-api/tests/test_action_authorization_contracts.py",
    "services/brain-api/tests/test_action_authorization_redaction.py",
    "services/brain-api/tests/test_action_authorization_decisions.py",
    "services/brain-api/tests/test_action_authorization_evaluator.py",
    "services/brain-api/tests/test_action_authorization_blockers.py",
    "services/brain-api/tests/test_action_authorization_audit.py",
    "services/brain-api/tests/test_action_authorization_api.py",
    "services/brain-api/tests/test_operator_actions_authorization_integration.py",
    "services/brain-api/tests/test_local_auth_action_authorization_integration.py",
    "services/brain-api/tests/test_local_session_action_authorization_integration.py",
    "services/brain-api/tests/test_role_matrix_action_authorization_integration.py",
    "services/brain-api/tests/test_operator_console_authorization_preview_static.py",
    "services/brain-api/tests/test_kernel_action_authorization_wiring.py",
    "services/brain-api/tests/test_visual_telemetry_action_authorization.py",
    "services/brain-api/tests/test_production_auth_architecture_docs.py",
    "services/brain-api/src/aion_brain/contracts/auth_runtime.py",
    "services/brain-api/src/aion_brain/auth_runtime/__init__.py",
    "services/brain-api/src/aion_brain/auth_runtime/actor_mapping.py",
    "services/brain-api/src/aion_brain/auth_runtime/audit.py",
    "services/brain-api/src/aion_brain/auth_runtime/blockers.py",
    "services/brain-api/src/aion_brain/auth_runtime/gate.py",
    "services/brain-api/src/aion_brain/auth_runtime/mock_claims.py",
    "services/brain-api/src/aion_brain/auth_runtime/query.py",
    "services/brain-api/src/aion_brain/auth_runtime/redaction.py",
    "services/brain-api/src/aion_brain/api/auth_runtime.py",
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
    "operator-console-static/demo-data/local-auth-status.json",
    "operator-console-static/demo-data/role-filtered-view-model.json",
    "scripts/auth-design-check.sh",
    "scripts/local-auth-check.sh",
    "scripts/auth-prototype-review.sh",
    "scripts/auth-no-go-regression.sh",
    "scripts/v02-implementation-authorization-no-go-regression.sh",
    "scripts/v02-implementation-authorization-preview-check.sh",
    "services/brain-api/src/aion_brain/contracts/local_auth.py",
    "services/brain-api/src/aion_brain/local_auth/__init__.py",
    "services/brain-api/src/aion_brain/local_auth/redaction.py",
    "services/brain-api/src/aion_brain/local_auth/roles.py",
    "services/brain-api/src/aion_brain/local_auth/identity.py",
    "services/brain-api/src/aion_brain/local_auth/context.py",
    "services/brain-api/src/aion_brain/local_auth/simulator.py",
    "services/brain-api/src/aion_brain/local_auth/access_matrix.py",
    "services/brain-api/src/aion_brain/local_auth/permission_matrix.py",
    "services/brain-api/src/aion_brain/local_auth/console_filter.py",
    "services/brain-api/src/aion_brain/local_auth/access_audit.py",
    "services/brain-api/src/aion_brain/local_auth/audit.py",
    "services/brain-api/src/aion_brain/local_auth/query.py",
    "services/brain-api/src/aion_brain/api/local_auth.py",
    "services/brain-api/src/aion_brain/identity/dev_auth.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/local_auth.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/local_auth.py",
    "packages/aion-sdk-python/tests/test_local_auth_resource.py",
    "packages/aion-sdk-python/tests/test_cli_local_auth.py",
    "services/brain-api/tests/test_auth_design_docs.py",
    "services/brain-api/tests/test_auth_prototype_review_docs.py",
    "services/brain-api/tests/test_v02_implementation_authorization_preview_docs.py",
    "services/brain-api/tests/test_v02_implementation_authorization_stabilization_docs.py",
    "scripts/v02-implementation-authorization-stabilization-no-go-regression.sh",
    "scripts/v02-implementation-authorization-stabilization-gate.sh",
    "operator-console-static/demo-data/v02-implementation-authorization-stabilization.json",
    "examples/release/v02-implementation-authorization-stabilization-gate.json",
    "examples/release/v02-authorization-stabilization-summary.json",
    "examples/release/v02-authorization-lifecycle-evidence-matrix.json",
    "docs/release/v02-implementation-authorization-closeout-checklist.md",
    "docs/release/v02-implementation-authorization-stabilization-no-go.md",
    "docs/release/v02-implementation-authorization-stabilization-gate.md",
    "docs/release/v02-authorization-stabilization-summary.md",
    "docs/release/v02-authorization-lifecycle-evidence-matrix.md",
    "docs/adr/0139-v02-implementation-authorization-stabilization.md",
    "services/brain-api/tests/test_local_auth_contracts.py",
    "services/brain-api/tests/test_local_auth_redaction.py",
    "services/brain-api/tests/test_local_auth_roles.py",
    "services/brain-api/tests/test_local_auth_identity.py",
    "services/brain-api/tests/test_local_auth_context.py",
    "services/brain-api/tests/test_local_auth_simulator.py",
    "services/brain-api/tests/test_local_auth_access_matrix.py",
    "services/brain-api/tests/test_local_auth_access_audit.py",
    "services/brain-api/tests/test_local_auth_audit.py",
    "services/brain-api/tests/test_local_auth_api.py",
    "services/brain-api/tests/test_operator_console_role_filtering.py",
    "services/brain-api/tests/test_kernel_local_auth_wiring.py",
    "services/brain-api/tests/test_visual_telemetry_local_auth.py",
    "docs/auth/local-session-prototype.md",
    "docs/auth/local-session-boundary.md",
    "docs/auth/session-safety-audit.md",
    "docs/auth/session-preview-console-panel.md",
    "docs/auth/future-session-implementation-plan.md",
    "docs/adr/0086-read-only-local-session-prototype.md",
    "examples/auth/local-session-preview-request.json",
    "examples/auth/local-session-status.json",
    "examples/auth/local-session-boundary-audit-request.json",
    "examples/auth/role-aware-session-context.json",
    "operator-console-static/demo-data/local-session-status.json",
    "operator-console-static/demo-data/local-session-preview.json",
    "scripts/local-session-check.sh",
    "services/brain-api/src/aion_brain/contracts/local_session.py",
    "services/brain-api/src/aion_brain/local_session/__init__.py",
    "services/brain-api/src/aion_brain/local_session/redaction.py",
    "services/brain-api/src/aion_brain/local_session/preview.py",
    "services/brain-api/src/aion_brain/local_session/context.py",
    "services/brain-api/src/aion_brain/local_session/boundary.py",
    "services/brain-api/src/aion_brain/local_session/audit.py",
    "services/brain-api/src/aion_brain/local_session/query.py",
    "services/brain-api/src/aion_brain/api/local_session.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/local_session.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/local_session.py",
    "packages/aion-sdk-python/tests/test_local_session_resource.py",
    "packages/aion-sdk-python/tests/test_cli_local_session.py",
    "services/brain-api/tests/test_local_session_contracts.py",
    "services/brain-api/tests/test_local_session_redaction.py",
    "services/brain-api/tests/test_local_session_preview.py",
    "services/brain-api/tests/test_local_session_context.py",
    "services/brain-api/tests/test_local_session_boundary.py",
    "services/brain-api/tests/test_local_session_audit.py",
    "services/brain-api/tests/test_local_session_api.py",
    "services/brain-api/tests/test_operator_console_session_preview.py",
    "services/brain-api/tests/test_kernel_local_session_wiring.py",
    "services/brain-api/tests/test_visual_telemetry_local_session.py",
    "services/brain-api/tests/test_connector_authorization_matrix.py",
    "services/brain-api/src/aion_brain/connector_credentials/authorization.py",
    "services/brain-api/tests/test_connector_credentials_authorization.py",
}

blocked_package_names = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
}
blocked_build_prefixes = (
    "vite.config.",
    "next.config.",
    "tailwind.config.",
    "webpack.config.",
)

for name in [*changed, *untracked]:
    path = Path(name)
    basename = path.name
    if basename in blocked_package_names or any(
        basename.startswith(prefix) for prefix in blocked_build_prefixes
    ):
        raise SystemExit(f"frontend package or build file changed: {name}")
    if name.startswith("infra/postgres/migrations/"):
        raise SystemExit(f"AION-093 must not add a migration: {name}")
    if name.startswith("services/brain-api/src/aion_brain/api/auth") and name not in allowed_auth_paths:
        raise SystemExit(f"AION-093 must not add an auth API route: {name}")
    if "auth" in name.lower() and name not in allowed_auth_paths:
        raise SystemExit(f"unexpected auth runtime or artifact path: {name}")

print("Auth examples valid and runtime boundaries clean")
PY

echo "Auth design check PASS"
