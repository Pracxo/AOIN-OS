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
