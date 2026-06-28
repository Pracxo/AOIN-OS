# UI Release Gate

## Purpose

AION-100 defines the static Operator Console UI release gate. The gate proves
the local prototype remains read-only, dependency-free, local-only, and safe to
use as a post-v0.1 operator platform checkpoint.

## Why UI release gate exists

AION-089 through AION-099 added static console panels for module lifecycle,
model provider hardening, governed operator actions, local auth, local session,
role filtering, dry-run action authorization, and disabled auth runtime. The UI
release gate gives those surfaces one canonical safety check before any future
UI framework, production auth, or runtime UI work is considered.

## What it checks

`./scripts/ui-release-gate.sh` runs the existing static and milestone checks:

- `operator-console-static-check.sh`
- `module-lifecycle-dashboard-check.sh`
- `provider-dashboard-check.sh`
- `operator-actions-check.sh`
- `local-auth-check.sh`
- `local-session-check.sh`
- `role-filter-check.sh`
- `action-authorization-check.sh`
- `auth-runtime-check.sh`
- `static-console-safety-check.sh`

It also validates the UI release docs, ADR, examples, and console artifacts.

## What it blocks

The gate blocks frontend dependencies, build tooling, external scripts, CDN
URLs, non-local API origins, write HTTP verbs, activation controls, execution
controls, provider-call controls, login forms, credential fields, token fields,
cookie fields, session persistence, protected prompt rendering, hidden
reasoning rendering, secret rendering, package install instructions, and
production UI claims.

## How to run

```bash
./scripts/ui-release-gate.sh
```

Run the narrower static-only check with:

```bash
./scripts/static-console-safety-check.sh
```

## Expected output

The expected final line is:

```text
UI release gate PASS
```

The narrower static check should print:

```text
Static console safety check PASS
```

## Relationship to AION-089 through AION-099

- AION-089 created the static local console prototype.
- AION-090 added the read-only module lifecycle dashboard.
- AION-091 added model provider hardening dashboard evidence.
- AION-092 added governed operator action preview panels.
- AION-094 added local auth status and role filtering.
- AION-095 added read-only local session preview.
- AION-096 added role-aware console filtering.
- AION-097 added dry-run action authorization evidence.
- AION-099 added disabled auth runtime status and mock claims preview.

## No-go conditions

Any failed gate condition is a release blocker. The static console must not add
production auth, login/logout behavior, credentials, token issuance, cookie
issuance, persisted sessions, provider runtime, external calls, write actions,
activation, execution, code loading, runtime registration, package files, or a
production-ready UI claim.

## Future UI release path

Future UI work must start from this gate, keep the static checkpoint passing,
and add a new architecture decision before introducing a framework, production
auth, governed write paths, runtime UI state, or provider-backed identity.

## AION-101 checkpoint relationship

AION-101 composes this gate into `./scripts/operator-platform-checkpoint.sh`.
The checkpoint does not loosen the UI release gate. It adds docs, examples, and
evidence validation that prove the AION-089 through AION-100 Operator Platform
phase is closed while the static console remains local, read-only,
dependency-free, and not production UI.

## AION-102 stabilization relationship

AION-102 composes this gate into `./scripts/operator-platform-regression.sh`
and `./scripts/operator-platform-freeze-gate.sh`. The stabilization layer keeps
the UI release gate mandatory and adds long-running regression evidence before
future UI, auth, activation, provider, connector, or write-path planning.
