# Connector Long-Running Regression Matrix

## Purpose

The AION-116 long-running regression matrix records the connector gates that
must remain green after the AION-115 platform checkpoint. Each row has an
expected safe value and becomes a release blocker if it fails.

## Matrix

| Area | Command or evidence | Expected safe value | Release blocker if failed |
| --- | --- | --- | --- |
| connector boundary checks | `./scripts/connector-boundary-design-check.sh` and `./scripts/connector-no-go-regression.sh` | connector boundary remains design-only | yes |
| runtime disabled checks | `./scripts/connector-runtime-review.sh` | `connector_runtime_enabled=false` | yes |
| no-external-call checks | `./scripts/connector-runtime-no-external-call-regression.sh` | `external_calls_enabled=false` | yes |
| simulator checks | `./scripts/connector-simulator-check.sh` and `./scripts/connector-simulator-no-go-regression.sh` | simulator evidence is synthetic-only | yes |
| policy checks | `./scripts/connector-policy-check.sh` and `./scripts/connector-policy-no-go-regression.sh` | runtime allow paths remain denied | yes |
| sandbox checks | `./scripts/connector-sandbox-check.sh` and `./scripts/connector-sandbox-no-go-regression.sh` | `sandbox_execution_enabled=false` | yes |
| credential checks | `./scripts/connector-credential-check.sh` and `./scripts/connector-credential-no-go-regression.sh` | `credentials_present=false` and `token_storage_enabled=false` | yes |
| release gate checks | `./scripts/connector-release-gate.sh`, `./scripts/connector-safety-freeze.sh`, and `./scripts/connector-release-no-go-regression.sh` | release gate passes with implementation approval false | yes |
| checkpoint checks | `./scripts/connector-platform-checkpoint.sh` and `./scripts/connector-platform-freeze-check.sh` | checkpoint passes with runtime disabled | yes |
| docs checks | `./scripts/docs-check.sh` and `./scripts/final-docs-audit.sh` | docs remain complete and linked | yes |
| static console checks | `operator-console-static/demo-data/connector-platform-stabilization.json` and `operator-console-static/demo-data/connector-phase-freeze-gate.json` | static evidence is read-only and bundled | yes |
| SDK/CLI preview-only checks | `docs/sdk.md` and `docs/cli.md` | preview-only; no implementation commands | yes |
| boundary checks | `./scripts/verify-no-domain-drift.sh` and `./scripts/boundary-check.sh` | no domain drift or boundary violation | yes |
| package drift checks | `./scripts/connector-platform-regression.sh` | `package_files_added=false` | yes |
| migration drift checks | `./scripts/connector-platform-regression.sh` | `migrations_added=false` | yes |
| implementation approval checks | `./scripts/connector-platform-stabilization-gate.sh` | `implementation_approved=false` | yes |

## Long-Running Cadence

The matrix should run before any future connector implementation ADR is
reviewed, after any connector documentation change, after any static console
connector evidence change, and before a release branch treats connector
artifacts as stable.

## Stable Baseline Values

- `connector_runtime_enabled=false`
- `external_calls_enabled=false`
- `credentials_present=false`
- `token_storage_enabled=false`
- `sandbox_execution_enabled=false`
- `connector_activation_enabled=false`
- `route_registration_enabled=false`
- `implementation_approved=false`
- `package_files_added=false`
- `migrations_added=false`

These values are the expected safe value for AION-116. Any true value is a
release blocker unless a future ADR explicitly approves a narrower
implementation boundary and updates this matrix.
