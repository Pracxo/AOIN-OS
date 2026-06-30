# Connector Phase Closeout Checklist

## Purpose

This checklist records the AION-115 closeout criteria for the connector phase.
It is review evidence and does not approve implementation.

## Closeout Criteria

- docs complete
- examples valid
- scripts executable
- release gate passing
- safety freeze passing
- no-go regression passing
- static console preview-only
- SDK/CLI preview-only
- no runtime enablement
- no external calls
- no credentials/tokens
- no sandbox execution
- no migrations
- no package files

## Required Local Commands

```bash
./scripts/connector-platform-checkpoint.sh
./scripts/connector-platform-freeze-check.sh
./scripts/connector-release-gate.sh
./scripts/connector-safety-freeze.sh
./scripts/connector-release-no-go-regression.sh
./scripts/connector-runtime-review.sh
./scripts/connector-simulator-check.sh
./scripts/connector-policy-check.sh
./scripts/connector-sandbox-check.sh
./scripts/connector-credential-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
./scripts/check.sh
git diff --check
```

## Static Console Closeout

The static console may show checkpoint and closeout demo data from bundled JSON.
It must remain read-only and must not add inputs, credential fields, token
fields, runtime buttons, external-call controls, activation controls, browser
storage, package dependencies, or build steps.

## SDK/CLI Closeout

SDK and CLI docs may reference local verification scripts and preview-only
resources. AION-115 adds no SDK resource, CLI command implementation, client
method, runtime route, or package dependency.

## Closeout Decision

The connector phase is closed only when the checkpoint and freeze scripts pass
and the safe-state flags remain disabled.

## AION-116 Stabilization Closeout

After AION-116, connector closeout also requires:

```bash
./scripts/connector-platform-regression.sh
./scripts/connector-platform-stabilization-gate.sh
```

The stabilization scripts must pass with connector implementation unapproved,
runtime disabled, external calls absent, credentials/tokens absent, sandbox
execution absent, activation disabled, route registration disabled, package
files absent, and migrations absent.
