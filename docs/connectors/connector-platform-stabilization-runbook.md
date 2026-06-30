# Connector Platform Stabilization Runbook

## Purpose

AION-116 stabilizes the connector platform checkpoint after AION-115 with a
long-running regression matrix and a connector phase freeze gate. The runbook
defines how connector evidence is checked before future connector implementation
work can be proposed.

This is stabilization evidence only. It does not approve connector
implementation, runtime behavior, external calls, credential storage, token
storage, sandbox execution, activation, route registration, write execution, or
tool execution.

## Scope

The stabilization scope covers the connector boundary, disabled runtime
preview, runtime review gate, synthetic simulator, policy catalog, sandbox
design, credential architecture, release gate, safety freeze, platform
checkpoint, static console evidence, SDK and CLI preview documentation, and
docs/boundary audits.

Out of scope:

- connector runtime implementation
- provider or connector SDK dependency
- external network client
- credential or token storage
- OAuth, OIDC, or SAML runtime
- sandbox execution
- module activation, capability activation, code loading, or runtime
  registration
- API execution route, SDK resource implementation, or CLI command
  implementation
- database migration or package manager file

## Required Connector Gates

The stabilization workflow requires these gates to pass:

```bash
./scripts/connector-platform-regression.sh
./scripts/connector-platform-stabilization-gate.sh
./scripts/connector-platform-checkpoint.sh
./scripts/connector-platform-freeze-check.sh
./scripts/connector-release-gate.sh
./scripts/connector-safety-freeze.sh
./scripts/connector-release-no-go-regression.sh
./scripts/connector-runtime-review.sh
./scripts/connector-runtime-no-external-call-regression.sh
./scripts/connector-simulator-check.sh
./scripts/connector-simulator-no-go-regression.sh
./scripts/connector-policy-check.sh
./scripts/connector-policy-no-go-regression.sh
./scripts/connector-sandbox-check.sh
./scripts/connector-sandbox-no-go-regression.sh
./scripts/connector-credential-check.sh
./scripts/connector-credential-no-go-regression.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
```

## Stabilization Workflow

1. Confirm the repository is on the connector stabilization branch.
2. Confirm the connector checkpoint artifacts from AION-115 are present.
3. Run `./scripts/connector-platform-regression.sh`.
4. Run `./scripts/connector-platform-stabilization-gate.sh`.
5. Review the stabilization evidence examples and static console data.
6. Confirm all safe-state values remain false where required:
   `connector_runtime_enabled=false`, `external_calls_enabled=false`,
   `credentials_present=false`, `token_storage_enabled=false`,
   `sandbox_execution_enabled=false`, `connector_activation_enabled=false`,
   `route_registration_enabled=false`, `implementation_approved=false`,
   `package_files_added=false`, and `migrations_added=false`.
7. Treat any new connector implementation proposal as blocked until a future ADR
   explicitly approves a narrow runtime boundary.

## CI Workflow

CI should call `./scripts/connector-platform-regression.sh` from the repository
root. The script uses repo-local portable search helpers and CI-safe Git
comparison handling. When the stabilization gate runs inside pytest or another
aggregate gate, the full repository check is deferred to the outer gate to avoid
nested full-check recursion.

CI failures are release blockers when they indicate runtime enablement,
external calls, credential/token storage, sandbox execution, activation, route
registration, package files, migrations, API execution routes, SDK/CLI
implementation drift, docs drift, or missing stabilization evidence.

## Manual Verification Workflow

Manual verification runs from the repository root:

```bash
./scripts/connector-platform-regression.sh
./scripts/connector-platform-stabilization-gate.sh
./scripts/check.sh
git diff --check
```

The expected result is a passing regression matrix, a passing stabilization
gate, a passing repository check, and no whitespace errors.

## Failure Triage

| Failure | Meaning | First triage step |
| --- | --- | --- |
| Missing stabilization doc | The checkpoint is not fully documented. | Restore the missing document and rerun the gate. |
| Unsafe safe-state value | A connector capability may have been enabled. | Revert the enablement and rerun no-go regressions. |
| External-call pattern | A runtime egress path may have appeared. | Remove the network path and rerun release/no-go gates. |
| Credential or token marker | Secret material or storage may have appeared. | Remove the value or storage path and rerun credential gates. |
| Sandbox execution marker | Sandbox runtime behavior may have appeared. | Remove execution behavior and rerun sandbox gates. |
| Package or migration file | Stabilization scope drifted into implementation. | Remove the dependency or migration and rerun the full gate. |

## Rollback Path

Rollback removes only the unsafe stabilization change. It does not move,
delete, or recreate `aion-v0.1.0` and does not mutate the v0.1 release
baseline. After rollback, rerun the connector regression script, stabilization
gate, docs checks, boundary checks, and full repository check.

## Release Blocker Conditions

Release is blocked if any of these conditions are found:

- `connector_runtime_enabled=true`
- `external_calls_enabled=true`
- `credentials_present=true`
- `token_storage_enabled=true`
- `sandbox_execution_enabled=true`
- `connector_activation_enabled=true`
- `route_registration_enabled=true`
- `implementation_approved=true`
- package manager file added
- migration added
- API execution route added
- SDK resource or CLI command implementation added
- privileged bypass added
- `aion-v0.1.0` tag moved, deleted, or recreated

## No-Go Conditions

The connector phase remains frozen after AION-116. No future work may treat this
runbook, the regression matrix, the stabilization gate, or static console data
as approval to implement runtime connectors, call external systems, store
credentials or tokens, execute sandbox code, activate modules, register
connector routes, execute tools, execute action proposals, or perform write
paths.
