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
    if path.name.startswith("request-identity-"):
        continue
    if path.name.startswith("actor-context-"):
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
    "docs/auth/actor-context-trust-boundary.md",
    "docs/auth/development-identity-simulation.md",
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
    "docs/adr/0151-v02-actor-context-trust-boundary-remediation.md",
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
    "examples/auth/actor-context-anonymous-resolution.json",
    "examples/auth/actor-context-request-identity-resolution.json",
    "examples/auth/actor-context-development-simulation.json",
    "examples/auth/actor-context-resolution-audit-event.json",
    "examples/auth/actor-context-resolution-provenance.json",
    "examples/auth/actor-context-resolution-diagnostics.json",
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
    "operator-console-static/demo-data/actor-context-trust-boundary.json",
    "operator-console-static/demo-data/actor-context-runtime-hold.json",
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
    "services/brain-api/tests/test_dev_auth_context.py",
    "services/brain-api/src/aion_brain/contracts/actor_context_resolution.py",
    "services/brain-api/src/aion_brain/production_auth/actor_context.py",
    "services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py",
    "services/brain-api/tests/test_actor_context_audit_provenance.py",
    "services/brain-api/tests/test_actor_context_concurrency.py",
    "services/brain-api/tests/test_actor_context_development_simulation.py",
    "services/brain-api/tests/test_actor_context_diagnostics.py",
    "services/brain-api/tests/test_actor_context_fail_closed.py",
    "services/brain-api/tests/test_actor_context_no_runtime_surface.py",
    "services/brain-api/tests/test_actor_context_payload_metadata.py",
    "services/brain-api/tests/test_actor_context_privilege_escalation.py",
    "services/brain-api/tests/test_actor_context_redaction.py",
    "services/brain-api/tests/test_actor_context_request_context_correlation.py",
    "services/brain-api/tests/test_actor_context_request_identity_precedence.py",
    "services/brain-api/tests/test_actor_context_resolution_contracts.py",
    "services/brain-api/tests/test_actor_context_route_integration.py",
    "services/brain-api/tests/test_actor_context_trust_boundary_docs.py",
    "scripts/production-auth-actor-context-trust-boundary-check.sh",
    "scripts/production-auth-actor-context-trust-boundary-runtime-hold.sh",
    "scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh",
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
    "scripts/v02-implementation-authorization-final-no-go-regression.sh",
    "scripts/v02-implementation-authorization-final-review.sh",
    "scripts/v02-runtime-enablement-guard-final-freeze.sh",
    "scripts/v02-authorization-track-closeout.sh",
    "scripts/v02-runtime-enablement-master-lock-freeze.sh",
    "scripts/v02-authorization-track-closeout-no-go-regression.sh",
    "scripts/v02-production-auth-authorization-check.sh",
    "scripts/v02-production-auth-runtime-guard-hold.sh",
    "scripts/v02-production-auth-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-stabilization-runtime-guard-hold.sh",
    "scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh",
    "scripts/lib/v02_production_auth_authorization.py",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "operator-console-static/demo-data/v02-implementation-authorization-stabilization.json",
    "operator-console-static/demo-data/v02-implementation-authorization-final-review.json",
    "operator-console-static/demo-data/v02-runtime-enablement-guard-final-lock.json",
    "operator-console-static/demo-data/v02-authorization-track-closeout.json",
    "operator-console-static/demo-data/v02-runtime-enablement-master-lock.json",
    "operator-console-static/demo-data/v02-production-auth-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json",
    "operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json",
    "operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json",
    "examples/release/v02-implementation-authorization-stabilization-gate.json",
    "examples/release/v02-authorization-stabilization-summary.json",
    "examples/release/v02-authorization-lifecycle-evidence-matrix.json",
    "examples/release/v02-implementation-authorization-final-review.json",
    "examples/release/v02-explicit-approval-record-closeout.json",
    "examples/release/v02-runtime-enablement-guard-final-lock.json",
    "examples/release/v02-authorization-final-evidence-matrix.json",
    "examples/release/v02-final-authorization-approval-guard.json",
    "examples/release/v02-authorization-track-closeout-report.json",
    "examples/release/v02-approval-chain-master-evidence.json",
    "examples/release/v02-runtime-enablement-master-lock.json",
    "examples/release/v02-explicit-approval-record-master-ledger.json",
    "examples/release/v02-implementation-authorization-final-status.json",
    "examples/release/v02-production-auth-implementation-authorization.json",
    "examples/release/v02-production-auth-explicit-approval-record.json",
    "examples/release/v02-production-auth-runtime-guard-hold.json",
    "examples/release/v02-production-auth-authorization-evidence-matrix.json",
    "examples/release/v02-production-auth-core-implementation-closeout.json",
    "examples/release/v02-production-auth-stabilization-authorization.json",
    "examples/release/v02-production-auth-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json",
    "docs/release/v02-implementation-authorization-closeout-checklist.md",
    "docs/release/v02-implementation-authorization-stabilization-no-go.md",
    "docs/release/v02-implementation-authorization-stabilization-gate.md",
    "docs/release/v02-authorization-stabilization-summary.md",
    "docs/release/v02-authorization-lifecycle-evidence-matrix.md",
    "docs/adr/0139-v02-implementation-authorization-stabilization.md",
    "docs/release/v02-implementation-authorization-final-checklist.md",
    "docs/release/v02-implementation-authorization-final-no-go.md",
    "docs/release/v02-implementation-authorization-final-review.md",
    "docs/release/v02-explicit-approval-record-closeout.md",
    "docs/release/v02-runtime-enablement-guard-final-lock.md",
    "docs/release/v02-authorization-final-evidence-matrix.md",
    "docs/release/v02-final-authorization-approval-guard.md",
    "docs/adr/0140-v02-implementation-authorization-final-review.md",
    "docs/release/v02-authorization-track-closeout-report.md",
    "docs/release/v02-approval-chain-master-evidence.md",
    "docs/release/v02-runtime-enablement-master-lock.md",
    "docs/release/v02-explicit-approval-record-master-ledger.md",
    "docs/release/v02-implementation-authorization-final-status.md",
    "docs/release/v02-authorization-track-closeout-no-go.md",
    "docs/release/v02-authorization-track-closeout-checklist.md",
    "docs/adr/0141-v02-authorization-track-closeout.md",
    "docs/release/v02-production-auth-implementation-authorization-transaction.md",
    "docs/release/v02-production-auth-explicit-approval-record.md",
    "docs/release/v02-production-auth-implementation-scope.md",
    "docs/release/v02-production-auth-runtime-guard-hold.md",
    "docs/release/v02-production-auth-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-authorization-no-go.md",
    "docs/release/v02-production-auth-authorization-checklist.md",
    "docs/adr/0142-v02-production-auth-implementation-authorization.md",
    "docs/release/v02-production-auth-core-implementation-closeout.md",
    "docs/release/v02-production-auth-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-stabilization-scope.md",
    "docs/release/v02-production-auth-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-stabilization-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-stabilization-authorization-no-go.md",
    "docs/release/v02-production-auth-stabilization-authorization-checklist.md",
    "docs/adr/0144-v02-production-auth-core-stabilization-authorization.md",
    "docs/auth/production-auth-core.md",
    "docs/auth/production-auth-core-runtime-boundary.md",
    "docs/auth/production-auth-policy-audit.md",
    "docs/release/v02-production-auth-core-implementation.md",
    "docs/release/v02-production-auth-core-runtime-hold.md",
    "docs/release/v02-production-auth-core-evidence-matrix.md",
    "docs/release/v02-production-auth-core-no-go.md",
    "docs/release/v02-production-auth-core-checklist.md",
    "docs/adr/0143-v02-disabled-production-auth-core-implementation.md",
    "examples/auth/production-auth-core-config.json",
    "examples/auth/production-auth-core-status.json",
    "examples/auth/production-auth-policy-decision.json",
    "examples/auth/production-auth-audit-event.json",
    "examples/auth/production-auth-provenance-record.json",
    "operator-console-static/demo-data/production-auth-core-status.json",
    "operator-console-static/demo-data/production-auth-runtime-hold.json",
    "scripts/production-auth-core-check.sh",
    "scripts/production-auth-core-runtime-hold.sh",
    "scripts/production-auth-core-no-go-regression.sh",
    "services/brain-api/src/aion_brain/contracts/production_auth.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/audit.py",
    "services/brain-api/src/aion_brain/production_auth/canonical.py",
    "services/brain-api/src/aion_brain/production_auth/config.py",
    "services/brain-api/src/aion_brain/production_auth/core.py",
    "services/brain-api/src/aion_brain/production_auth/diagnostics.py",
    "services/brain-api/src/aion_brain/production_auth/policy.py",
    "services/brain-api/src/aion_brain/production_auth/provenance.py",
    "services/brain-api/src/aion_brain/production_auth/reason_codes.py",
    "services/brain-api/tests/test_production_auth_stabilization_contracts.py",
    "services/brain-api/tests/test_production_auth_canonicalization.py",
    "services/brain-api/tests/test_production_auth_fingerprints.py",
    "services/brain-api/tests/test_production_auth_reason_codes.py",
    "services/brain-api/tests/test_production_auth_idempotency.py",
    "services/brain-api/tests/test_production_auth_concurrency.py",
    "services/brain-api/tests/test_production_auth_stabilization_redaction.py",
    "services/brain-api/tests/test_production_auth_stabilization_config_matrix.py",
    "services/brain-api/tests/test_production_auth_stabilization_kernel.py",
    "services/brain-api/tests/test_production_auth_stabilization_routes.py",
    "services/brain-api/tests/test_production_auth_stabilization_performance.py",
    "examples/auth/production-auth-stabilized-core-status.json",
    "examples/auth/production-auth-stabilized-policy-decision.json",
    "examples/auth/production-auth-stabilized-audit-event.json",
    "examples/auth/production-auth-stabilized-provenance-record.json",
    "examples/auth/production-auth-stabilized-diagnostics.json",
    "operator-console-static/demo-data/production-auth-core-stabilization.json",
    "operator-console-static/demo-data/production-auth-core-stabilization-runtime-hold.json",
    "docs/auth/production-auth-core-stabilization.md",
    "docs/auth/production-auth-canonical-evidence.md",
    "docs/release/v02-production-auth-core-stabilization.md",
    "docs/release/v02-production-auth-core-stabilization-evidence-matrix.md",
    "docs/release/v02-production-auth-core-stabilization-runtime-hold.md",
    "docs/release/v02-production-auth-core-stabilization-no-go.md",
    "docs/release/v02-production-auth-core-stabilization-checklist.md",
    "docs/adr/0145-v02-production-auth-core-stabilization.md",
    "docs/adr/0146-v02-production-auth-request-boundary-authorization.md",
    "docs/release/v02-production-auth-core-stabilization-closeout.md",
    "docs/release/v02-production-auth-request-boundary-authorization-transaction.md",
    "docs/release/v02-production-auth-request-boundary-scope.md",
    "docs/release/v02-production-auth-request-boundary-runtime-hold.md",
    "docs/release/v02-production-auth-request-boundary-authorization-checklist.md",
    "examples/release/v02-production-auth-core-stabilization-closeout.json",
    "examples/release/v02-production-auth-request-boundary-authorization.json",
    "examples/release/v02-production-auth-request-boundary-runtime-hold.json",
    "operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json",
    "scripts/v02-production-auth-request-boundary-authorization-check.sh",
    "scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh",
    "services/brain-api/tests/test_v02_production_auth_request_boundary_authorization_docs.py",
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/production_auth/verifier.py",
    "services/brain-api/src/aion_brain/production_auth/request_boundary.py",
    "services/brain-api/src/aion_brain/production_auth/request_middleware.py",
    "services/brain-api/src/aion_brain/production_auth/request_evidence.py",
    "services/brain-api/tests/test_request_identity_contracts.py",
    "services/brain-api/tests/test_request_identity_verifiers.py",
    "services/brain-api/tests/test_request_identity_boundary.py",
    "services/brain-api/tests/test_request_identity_middleware.py",
    "services/brain-api/tests/test_request_identity_app_factory.py",
    "services/brain-api/tests/test_request_identity_audit_provenance.py",
    "services/brain-api/tests/test_request_identity_concurrency.py",
    "services/brain-api/tests/test_request_identity_redaction.py",
    "services/brain-api/tests/test_request_identity_config.py",
    "services/brain-api/tests/test_request_identity_no_runtime_routes.py",
    "docs/auth/request-identity-boundary.md",
    "docs/auth/request-identity-runtime-boundary.md",
    "docs/auth/production-auth-core.md",
    "docs/auth/production-auth-core-runtime-boundary.md",
    "docs/auth/production-auth-core-stabilization.md",
    "docs/auth/future-auth-implementation-plan.md",
    "docs/auth/production-auth-release-gates.md",
    "docs/release/v02-production-auth-request-identity-boundary-implementation.md",
    "docs/release/v02-production-auth-request-identity-boundary-runtime-hold.md",
    "docs/release/v02-production-auth-request-identity-boundary-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-boundary-no-go.md",
    "docs/release/v02-production-auth-request-identity-boundary-checklist.md",
    "docs/adr/0147-v02-disabled-production-auth-request-identity-boundary.md",
    "examples/auth/request-identity-boundary-status.json",
    "examples/auth/request-identity-disabled-context.json",
    "examples/auth/request-identity-verification-result.json",
    "examples/auth/request-identity-audit-event.json",
    "examples/auth/request-identity-provenance-record.json",
    "operator-console-static/demo-data/production-auth-request-identity-boundary.json",
    "operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json",
    "docs/release/v02-production-auth-request-identity-boundary-closeout.md",
    "docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-request-identity-stabilization-scope.md",
    "docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-stabilization-no-go.md",
    "docs/release/v02-production-auth-request-identity-stabilization-checklist.md",
    "docs/release/v02-implementation-authorization-final-status.md",
    "docs/adr/0148-v02-production-auth-request-identity-stabilization-authorization.md",
    "examples/release/v02-production-auth-request-identity-boundary-closeout.json",
    "examples/release/v02-production-auth-request-identity-stabilization-authorization.json",
    "examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json",
    "services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py",
    "scripts/production-auth-request-identity-check.sh",
    "scripts/production-auth-request-identity-runtime-hold.sh",
    "scripts/production-auth-request-identity-no-go-regression.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
    "scripts/auth-design-check.sh",
    "scripts/local-auth-check.sh",
    "scripts/v02-production-auth-authorization-check.sh",
    "scripts/v02-production-auth-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh",
    "scripts/production-auth-core-stabilization-check.sh",
    "scripts/production-auth-core-stabilization-runtime-hold.sh",
    "scripts/production-auth-core-stabilization-no-go-regression.sh",
    "services/brain-api/src/aion_brain/contracts/production_auth.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/config.py",
    "services/brain-api/src/aion_brain/production_auth/core.py",
    "services/brain-api/src/aion_brain/production_auth/policy.py",
    "services/brain-api/src/aion_brain/production_auth/audit.py",
    "services/brain-api/src/aion_brain/production_auth/provenance.py",
    "services/brain-api/src/aion_brain/production_auth/diagnostics.py",
    "services/brain-api/tests/test_production_auth_contracts.py",
    "services/brain-api/tests/test_production_auth_config.py",
    "services/brain-api/tests/test_production_auth_core.py",
    "services/brain-api/tests/test_production_auth_policy.py",
    "services/brain-api/tests/test_production_auth_audit_provenance.py",
    "services/brain-api/tests/test_production_auth_diagnostics.py",
    "services/brain-api/tests/test_kernel_production_auth_wiring.py",
    "services/brain-api/tests/test_production_auth_no_runtime_routes.py",
    "services/brain-api/tests/test_v02_authorization_track_closeout_docs.py",
    "services/brain-api/tests/test_v02_production_auth_authorization_docs.py",
    "services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py",
    "services/brain-api/tests/test_v02_implementation_authorization_final_review_docs.py",
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

aion158_auth_paths = {
    "docs/adr/0149-v02-production-auth-request-identity-stabilization.md",
    "docs/auth/production-auth-release-gates.md",
    "docs/auth/request-identity-asgi-middleware.md",
    "docs/auth/request-identity-boundary.md",
    "docs/auth/request-identity-runtime-boundary.md",
    "docs/auth/request-identity-stabilization.md",
    "docs/release/v02-production-auth-request-identity-boundary-checklist.md",
    "docs/release/v02-production-auth-request-identity-boundary-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-boundary-implementation.md",
    "docs/release/v02-production-auth-request-identity-boundary-runtime-hold.md",
    "docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-request-identity-stabilization-checklist.md",
    "docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-request-identity-stabilization-no-go.md",
    "docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-request-identity-stabilization-runtime-hold.md",
    "docs/release/v02-production-auth-request-identity-stabilization-scope.md",
    "docs/release/v02-production-auth-request-identity-stabilization.md",
    "examples/auth/request-identity-audit-event.json",
    "examples/auth/request-identity-boundary-status.json",
    "examples/auth/request-identity-disabled-context.json",
    "examples/auth/request-identity-provenance-record.json",
    "examples/auth/request-identity-stabilized-audit-event.json",
    "examples/auth/request-identity-stabilized-boundary-status.json",
    "examples/auth/request-identity-stabilized-diagnostics.json",
    "examples/auth/request-identity-stabilized-disabled-context.json",
    "examples/auth/request-identity-stabilized-provenance-record.json",
    "examples/auth/request-identity-verification-result.json",
    "operator-console-static/demo-data/production-auth-request-identity-stabilization-runtime-hold.json",
    "operator-console-static/demo-data/production-auth-request-identity-stabilization.json",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/production-auth-core-no-go-regression.sh",
    "scripts/production-auth-core-stabilization-no-go-regression.sh",
    "scripts/production-auth-request-identity-no-go-regression.sh",
    "scripts/production-auth-request-identity-stabilization-check.sh",
    "scripts/production-auth-request-identity-stabilization-no-go-regression.sh",
    "scripts/production-auth-request-identity-stabilization-runtime-hold.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/request_boundary.py",
    "services/brain-api/src/aion_brain/production_auth/request_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/request_middleware.py",
}

aion159_auth_paths = {
    "AGENTS.md",
    "README.md",
    "docs/adr/0150-v02-actor-context-trust-boundary-authorization.md",
    "docs/adr/README.md",
    "docs/architecture.md",
    "docs/auth/future-auth-implementation-plan.md",
    "docs/auth/production-auth-release-gates.md",
    "docs/auth/request-identity-boundary.md",
    "docs/auth/request-identity-runtime-boundary.md",
    "docs/auth/request-identity-stabilization.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/project-status.md",
    "docs/release/v02-actor-context-trust-boundary-authorization-transaction.md",
    "docs/release/v02-actor-context-trust-boundary-checklist.md",
    "docs/release/v02-actor-context-trust-boundary-evidence-matrix.md",
    "docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md",
    "docs/release/v02-actor-context-trust-boundary-no-go.md",
    "docs/release/v02-actor-context-trust-boundary-runtime-hold.md",
    "docs/release/v02-actor-context-trust-boundary-scope.md",
    "docs/release/v02-explicit-approval-record-master-ledger.md",
    "docs/release/v02-implementation-authorization-final-status.md",
    "docs/release/v02-production-auth-request-boundary-authorization-checklist.md",
    "docs/release/v02-production-auth-request-boundary-authorization-transaction.md",
    "docs/release/v02-production-auth-request-identity-boundary-checklist.md",
    "docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-request-identity-stabilization-checklist.md",
    "docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-request-identity-stabilization-runtime-hold.md",
    "docs/release/v02-production-auth-request-identity-stabilization.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/release/v02-request-identity-stabilization-closeout.md",
    "docs/visual-brain.md",
    "examples/operator-console/static-console-navigation-map.json",
    "examples/release/v02-actor-context-trust-boundary-authorization.json",
    "examples/release/v02-actor-context-trust-boundary-evidence-matrix.json",
    "examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json",
    "examples/release/v02-actor-context-trust-boundary-runtime-hold.json",
    "examples/release/v02-production-auth-request-identity-stabilization-authorization.json",
    "examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json",
    "examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-request-identity-stabilization-closeout.json",
    "operator-console-static/README.md",
    "operator-console-static/app.js",
    "operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json",
    "operator-console-static/index.html",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/lib/v02_production_auth_authorization.py",
    "scripts/static-console-safety-check.sh",
    "scripts/static-console-ux-check.sh",
    "scripts/v02-actor-context-trust-boundary-authorization-check.sh",
    "scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-authorization-check.sh",
    "scripts/v02-production-auth-request-boundary-authorization-check.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "services/brain-api/tests/test_static_console_ux_refinement.py",
    "services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py",
    "services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py",
}

aion161_auth_paths = {
    "AGENTS.md",
    "README.md",
    "docs/adr/0152-v02-offline-ed25519-identity-assertion-verification-authorization.md",
    "docs/adr/README.md",
    "docs/auth/actor-context-trust-boundary.md",
    "docs/auth/development-identity-simulation.md",
    "docs/auth/future-auth-implementation-plan.md",
    "docs/auth/production-auth-release-gates.md",
    "docs/auth/request-identity-boundary.md",
    "docs/auth/request-identity-runtime-boundary.md",
    "docs/architecture.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/project-status.md",
    "docs/release/v02-actor-context-trust-boundary-authorization-transaction.md",
    "docs/release/v02-actor-context-trust-boundary-checklist.md",
    "docs/release/v02-actor-context-trust-boundary-evidence-matrix.md",
    "docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md",
    "docs/release/v02-actor-context-trust-boundary-remediation-closeout.md",
    "docs/release/v02-actor-context-trust-boundary-remediation.md",
    "docs/release/v02-actor-context-trust-boundary-runtime-hold.md",
    "docs/release/v02-explicit-approval-record-master-ledger.md",
    "docs/release/v02-implementation-authorization-final-status.md",
    "docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md",
    "docs/release/v02-offline-identity-assertion-verification-checklist.md",
    "docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md",
    "docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md",
    "docs/release/v02-offline-identity-assertion-verification-no-go.md",
    "docs/release/v02-offline-identity-assertion-verification-runtime-hold.md",
    "docs/release/v02-offline-identity-assertion-verification-scope.md",
    "docs/release/v02-offline-identity-assertion-verification-threat-model.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/visual-brain.md",
    "examples/release/v02-actor-context-trust-boundary-authorization.json",
    "examples/release/v02-actor-context-trust-boundary-evidence-matrix.json",
    "examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json",
    "examples/release/v02-actor-context-trust-boundary-remediation-closeout.json",
    "examples/release/v02-actor-context-trust-boundary-runtime-hold.json",
    "examples/release/v02-offline-identity-assertion-verification-authorization.json",
    "examples/release/v02-offline-identity-assertion-verification-evidence-matrix.json",
    "examples/release/v02-offline-identity-assertion-verification-explicit-approval-record.json",
    "examples/release/v02-offline-identity-assertion-verification-runtime-hold.json",
    "operator-console-static/README.md",
    "operator-console-static/app.js",
    "operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json",
    "operator-console-static/demo-data/v02-offline-identity-assertion-verification-authorization.json",
    "operator-console-static/index.html",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/lib/v02_production_auth_authorization.py",
    "scripts/production-auth-actor-context-trust-boundary-check.sh",
    "scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh",
    "scripts/v02-actor-context-trust-boundary-authorization-check.sh",
    "scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh",
    "scripts/v02-offline-identity-assertion-verification-authorization-check.sh",
    "scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-request-boundary-authorization-check.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "services/brain-api/tests/test_actor_context_trust_boundary_docs.py",
    "services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py",
    "services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py",
    "services/brain-api/tests/test_v02_production_auth_request_boundary_authorization_docs.py",
    "services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py",
    "services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py",
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
    if (
        "auth" in name.lower()
        and name not in allowed_auth_paths
        and name not in aion158_auth_paths
        and name not in aion159_auth_paths
        and name not in aion161_auth_paths
    ):
        raise SystemExit(f"unexpected auth runtime or artifact path: {name}")

print("Auth examples valid and runtime boundaries clean")
PY

echo "Auth design check PASS"
