# Connector Stabilization Evidence Pack

## Purpose

This evidence pack records the AION-116 stabilization artifacts and the local
scripts that prove the connector phase remains frozen after AION-115.

## Evidence Table

| Evidence | Gate script | Expected output | Release blocker | Notes |
| --- | --- | --- | --- | --- |
| Stabilization runbook | `./scripts/connector-platform-regression.sh` | document exists | yes | Records manual and CI workflows. |
| Long-running regression matrix | `./scripts/connector-platform-regression.sh` | matrix exists and names required checks | yes | Defines expected safe values. |
| Connector phase freeze gate | `./scripts/connector-platform-stabilization-gate.sh` | `Connector platform stabilization gate PASS` | yes | Aggregates regression and full check outside nested contexts. |
| Safety baseline lock | `./scripts/connector-platform-regression.sh` | all baseline booleans are safe | yes | Locks runtime, external, credential, token, sandbox, activation, route, package, and migration values. |
| Regression examples | `./scripts/connector-platform-regression.sh` | valid JSON with synthetic evidence | yes | Contains no endpoints, secrets, tokens, credentials, raw prompts, or hidden reasoning. |
| Static console stabilization data | `./scripts/connector-platform-regression.sh` | bundled read-only JSON exists | yes | Adds no input controls, build step, package file, or runtime route. |
| ADR 0107 | `./scripts/connector-platform-regression.sh` | ADR exists and is indexed | yes | Future implementation requires a new ADR. |
| Full repository check | `./scripts/connector-platform-stabilization-gate.sh` | repository health pass or deferred to outer gate | yes | Direct manual execution remains strict. |

## Stabilization Artifacts

- `docs/connectors/connector-platform-stabilization-runbook.md`
- `docs/connectors/connector-long-running-regression-matrix.md`
- `docs/connectors/connector-phase-freeze-gate.md`
- `docs/connectors/connector-stabilization-evidence-pack.md`
- `docs/connectors/connector-safety-baseline-lock.md`
- `docs/connectors/connector-regression-evidence.md`
- `docs/adr/0107-connector-platform-stabilization-gate.md`
- `examples/connectors/connector-platform-stabilization-result.json`
- `examples/connectors/connector-long-running-regression-matrix.json`
- `examples/connectors/connector-phase-freeze-gate-result.json`
- `examples/connectors/connector-stabilization-evidence-pack.json`
- `operator-console-static/demo-data/connector-platform-stabilization.json`
- `operator-console-static/demo-data/connector-phase-freeze-gate.json`
- `scripts/connector-platform-regression.sh`
- `scripts/connector-platform-stabilization-gate.sh`

## Evidence Decision

The stabilization evidence proves the connector phase can remain frozen and
reviewable. It does not approve connector implementation and does not authorize
runtime behavior.
