# AION Operator Console Static Prototype

This directory contains the AION-089 static local Operator Console prototype.
It is plain HTML, CSS, and JavaScript only.

## Boundaries

- local read-only prototype
- no build step
- no frontend dependency
- no package manager file
- no runtime UI claim
- no production auth claim
- no activation
- no execution
- no external calls
- no stored protected values

## Run Locally

Open the file directly:

```bash
open operator-console-static/index.html
```

Serve it locally:

```bash
python3 -m http.server 8090 --directory operator-console-static
open http://localhost:8090
open "http://localhost:8090?api=http://localhost:8080"
```

Validate the static contract:

```bash
./scripts/static-console-safety-check.sh
./scripts/ui-release-gate.sh
./scripts/operator-console-static-check.sh
./scripts/operator-console-static-demo.sh --offline-ok --skip-api
```

## Local Auth Panel

AION-094 adds a Local Auth Status panel backed by
`demo-data/local-auth-status.json` and `demo-data/role-filtered-view-model.json`.
The panel shows that production auth, credentials, sessions, external identity
provider integration, and write actions are disabled. It has no login form, no
credential input, no token input, and no session persistence.

## Local Session Panel

AION-095 adds a Local Session Preview panel backed by
`demo-data/local-session-status.json` and `demo-data/local-session-preview.json`.
The panel renders a synthetic dev-only session preview for role-aware console
filtering. It is not production auth, does not authenticate users, does not
issue tokens or cookies, and does not persist browser session state.

Validate the local session panel:

```bash
./scripts/local-session-check.sh
./scripts/operator-console-static-check.sh
```

## Module Lifecycle Dashboard

AION-090 adds a read-only Module Lifecycle Dashboard to the static console.
Open the Module Lifecycle navigation item to inspect the Generic Knowledge
Intelligence trail, expected activation blockers, synthetic mock runtime
output, and operator review checklist.

Offline demo files:

- `demo-data/module-lifecycle-dashboard.json`
- `demo-data/generic-knowledge-trail.json`
- `demo-data/module-activation-blockers.json`
- `demo-data/module-mock-runtime-trail.json`
- `demo-data/module-review-checklist.json`

Activation remains blocked. The dashboard does not load code, execute
capabilities, register runtime routes, call external services, or mutate Brain
records.

Validate the module dashboard:

```bash
./scripts/module-lifecycle-dashboard-check.sh
./scripts/operator-console-static-demo.sh --offline-ok --skip-api
```

## Operator Actions Panel

AION-092 adds a static Operator Actions panel for dry-run request previews,
blocked effects, blockers, and review records.

Offline demo files:

- `demo-data/operator-action-preview.json`
- `demo-data/operator-action-blockers.json`
- `demo-data/operator-action-review.json`

The panel does not run actions. It renders `execution_allowed=false`,
`external_calls_allowed=false`, `activation_allowed=false`, and
`would_execute=false`.

Validate the panel:

```bash
./scripts/operator-actions-check.sh
./scripts/operator-console-static-check.sh
./scripts/role-filter-check.sh
```

## Role Preview

The AION-096 role preview switcher is local demo data only. It exposes viewer,
operator, reviewer, admin, and auditor views while keeping `system_service`
internal and all privileged actions disabled.

## Action Authorization Panel

AION-097 adds a static Action Authorization panel backed by:

- `demo-data/action-authorization-preview.json`
- `demo-data/action-authorization-deny-matrix.json`

The panel displays dry-run authorization decisions and denied cases. It does
not expose execute, activation, external-call, login, credential, token,
cookie, or browser storage behavior.

## Auth Runtime Panel

AION-099 adds a disabled Auth Runtime panel backed by:

- `demo-data/auth-runtime-status.json`
- `demo-data/mock-claims-preview.json`

The panel displays disabled production auth status and a mock claims preview.
It has no login form, no logout control, no credential input, no token input,
and no session persistence.

## Connector Runtime Panel

AION-108 adds a disabled Connector Runtime panel backed by:

- `demo-data/connector-runtime-status.json`
- `demo-data/connector-boundary-preview.json`
- `demo-data/connector-simulation-preview.json`
- `demo-data/connector-policy-readiness.json`

The panel displays hard-off connector runtime flags, blockers, and mock-only
boundary preview evidence. It has no connector registration form, no credential
input, no token input, no route activation, and no external service egress.

AION-110 adds static connector simulator evidence to the same panel. The
simulator data is synthetic-only and never represents connector execution,
route registration, trusted ingress, credential use, token use, or external
egress.

## UI Release Gate

AION-100 adds the static UI release gate:

- `scripts/static-console-safety-check.sh`
- `scripts/ui-release-gate.sh`

The gate proves the static console remains read-only, local, dependency-free,
build-free, login-free, provider-call-free, activation-free, and
execution-free.

## Static Console UX Refinement

AION-103 adds dependency-free navigation groups, a skip link, section
shortcuts, visible focus states, a safety blocker view, and safe local command
copy cards.

Navigation groups:

- Platform
- Modules
- Providers
- Actions
- Auth and Sessions
- Evidence
- Safety

Copy support is limited to:

- `./scripts/ui-release-gate.sh`
- `./scripts/static-console-safety-check.sh`
- `./scripts/operator-platform-regression.sh`
- `./scripts/operator-platform-freeze-gate.sh`
- `./scripts/docs-check.sh`

The UX refinement adds no framework, package file, build step, login/logout
behavior, credential control, token or cookie issuance, session persistence,
provider call, write control, activation control, or execution control.

Validate the UX refinement:

```bash
./scripts/static-console-ux-check.sh
```
