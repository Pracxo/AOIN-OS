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
```
