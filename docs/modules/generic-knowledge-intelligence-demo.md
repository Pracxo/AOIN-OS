# Generic Knowledge Intelligence Demo

## Purpose

This demo proves the first post-v0.1 module ecosystem path with a metadata-only
module pack. It validates fixtures, shows the dry-run sequence, and confirms
that activation remains blocked by default.

The demo does not load code, install packages, register routes, activate
capabilities, execute tools, call external services, or mutate the v0.1 release
baseline.

## Local Prerequisites

- Run from the repository root.
- Keep the `aion-v0.1.0` tag untouched.
- Use the current post-v0.1 phase branch.
- For offline validation, no Docker stack or API is required.
- For optional API-backed dry-run checks, use only a local Brain API URL.

## Start From v0.1 Baseline

The module pack starts from the frozen v0.1 baseline. AION-084 adds examples,
docs, scripts, and tests only. It does not add database tables, API routes, SDK
resources, CLI commands, or runtime registration.

## Commands

Validate the module pack fixtures:

```bash
./scripts/module-pack-check.sh
```

Run the fully offline demo path:

```bash
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
```

Run optional local API-backed dry-run checks when the Brain API is available:

```bash
./scripts/generic-knowledge-demo.sh --offline-ok --api-url http://localhost:8080
```

The demo rejects non-local API URLs.

## Dry-Run Sequence

1. Run manifest validation against `manifest.json`.
2. Run extension intake dry-run using `intake-request.json`.
3. Create or inspect the module slot request fixture.
4. Validate the capability binding fixture.
5. Create or inspect the module mock profile fixture.
6. Run module mock invocation dry-run using `mock-invocation-request.json`.
7. Run conformance dry-run using `conformance-run-request.json`.
8. Run readiness assessment dry-run using `readiness-assessment-request.json`.
9. Create an activation request dry-run using `activation-request.json`.
10. Run activation gate dry-run using `activation-gate-request.json`.
11. Inspect expected blockers.
12. Record or inspect operator review using `operator-review-request.json`.

## Expected Output

Offline mode must report:

- JSON fixtures valid.
- Demo scripts executable.
- `activation_ready=false`.
- `activation_allowed=false`.
- `runtime_registration_allowed=false`.
- module mock runtime output is synthetic.
- module mock runtime execution flags remain false.
- Expected blockers include activation disabled, runtime registration disabled,
  and code loading disabled.

## Failure Handling

Stop the demo if any of these appear:

- executable payloads
- external dependencies
- source URLs
- route registration
- runtime registration
- capability activation
- controlled mode
- tool execution
- external service calls
- raw secret access
- domain workflow logic

If the local API is unavailable and `--offline-ok` is set, the demo reports the
API as unavailable and completes offline validation only.

## Operator Console Mapping

AION-087 maps the module demo into a future Operator Console view. The view is
read/review/dry-run only and uses existing fixtures plus existing API/CLI
paths. It must show activation blockers, conformance state, readiness state,
operator review, and mock-runtime evidence without enabling activation.

The future view must not load code, install packages, register routes,
activate modules, activate capabilities, execute tools, call external
services, expose raw prompts, expose hidden reasoning, or reveal secrets.

## Static Module Dashboard Mapping

AION-090 renders this demo path in the static Operator Console Module
Lifecycle Dashboard. The dashboard uses local demo JSON to show the same
manifest, intake, slot, binding, validation, conformance, readiness, activation
request, activation gate, blocker, mock runtime, and operator review path.

The dashboard is read-only. It does not activate modules, load code, register
routes, execute capabilities, call external services, mutate Brain records, or
change the v0.1 release baseline.
