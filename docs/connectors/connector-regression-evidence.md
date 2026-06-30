# Connector Regression Evidence

## Purpose

This document records how AION-116 regression evidence is produced and what a
failure means. It is stabilization evidence only and does not approve connector
implementation.

## Evidence Rows

| Commands run | Expected result | Failure meaning | Remediation path | Next review point |
| --- | --- | --- | --- | --- |
| `./scripts/connector-platform-regression.sh` | `connector platform regression PASS` | The long-running connector matrix is incomplete or unsafe. | Restore missing docs/examples/static data or remove unsafe enablement. | Re-run before any connector ADR review. |
| `./scripts/connector-platform-stabilization-gate.sh` | `connector platform stabilization gate PASS` | The connector phase is not frozen safely. | Fix the failing regression or full-check output. | Re-run before future connector implementation work. |
| `./scripts/connector-release-gate.sh` | `Connector release gate PASS` | Release gate evidence regressed. | Restore release evidence and no-go results. | Re-run before release branch work. |
| `./scripts/connector-safety-freeze.sh` | `Connector safety freeze PASS` | The safety freeze was weakened or missing. | Restore the frozen safe state. | Re-run before connector phase changes. |
| `./scripts/connector-runtime-review.sh` | runtime review pass | Connector runtime review evidence regressed. | Remove runtime enablement or restore review evidence. | Re-run before runtime ADR work. |
| `./scripts/connector-runtime-no-external-call-regression.sh` | no external-call pass | External-call surface may have appeared. | Remove network clients or egress paths. | Re-run before any egress proposal. |
| `./scripts/connector-simulator-check.sh` | simulator check pass | Synthetic simulator evidence regressed. | Restore synthetic-only simulator examples. | Re-run before simulator documentation changes. |
| `./scripts/connector-policy-check.sh` | policy check pass | Denial or traceability evidence regressed. | Restore deny rows and dry-run policy evidence. | Re-run before policy change review. |
| `./scripts/connector-sandbox-check.sh` | sandbox check pass | Sandbox design or no-go evidence regressed. | Remove execution paths or restore sandbox docs. | Re-run before sandbox ADR work. |
| `./scripts/connector-credential-check.sh` | credential check pass | Credential/token absence evidence regressed. | Remove storage paths or restore redacted examples. | Re-run before credential implementation proposal. |

## Next Review Point

The next connector review point is a future implementation ADR. Until that ADR
exists and passes the stabilization gate, the connector phase remains frozen and
implementation approval remains false.
