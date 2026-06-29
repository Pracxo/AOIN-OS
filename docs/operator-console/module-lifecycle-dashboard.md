# Module Lifecycle Dashboard

## Purpose

AION-090 extends the static local Operator Console prototype with a read-only
Module Lifecycle Dashboard. It makes the Generic Knowledge Intelligence module
trail visible before any real UI, activation path, or runtime module work is
enabled.

## What the dashboard shows

The dashboard shows the metadata-only path:

```text
extension manifest
  -> extension intake
  -> module slot
  -> capability bindings
  -> binding validation
  -> conformance
  -> readiness
  -> module activation request
  -> activation gate
  -> activation blockers
  -> module mock runtime
  -> operator review
```

It also shows local evidence refs, safe blockers, synthetic mock runtime
summaries, and review-only checklist entries.

## What it does not do

The dashboard does not activate a module, execute a capability, call a model
provider, register runtime routes, mutate Brain records, send write requests,
store credentials, expose raw prompts, expose hidden reasoning, or load code.

## Stage model

Every stage is rendered from static JSON or an existing read-only view-model
response. Stage records include status, evidence refs, blockers, warnings,
allowed descriptors, and forbidden descriptors. Allowed descriptors are display
labels only.

## Generic Knowledge Intelligence trail

Generic Knowledge Intelligence is the first trail because it is generic,
metadata-only, and already has dry-run evidence. Its five capability keys are:

- `generic.knowledge.retrieve`
- `generic.knowledge.summarize`
- `generic.knowledge.ground`
- `generic.knowledge.explain`
- `generic.knowledge.answer`

All five remain inactive with `controlled_supported=false`,
`dry_run_supported=true`, `activation_allowed=false`,
`external_calls_made=false`, and `code_loaded=false`.

## Safe blockers

The expected blockers are successful safety evidence:

- `activation_disabled`
- `code_loading_disabled`
- `package_install_disabled`
- `dynamic_route_registration_disabled`
- `runtime_registration_disabled`

No blocker is bypassable. The dashboard should make blockers visible rather
than hide them.

## Read-only review

Operator review can inspect evidence and interpret readiness. Review is not
activation. Review cannot approve code loading, route registration, runtime
registration, controlled execution, external calls, provider calls, or tool
execution.

## Offline fallback

If the local Brain API is unavailable, the static console renders local JSON
from `operator-console-static/demo-data/`. The module dashboard files are:

- `module-lifecycle-dashboard.json`
- `generic-knowledge-trail.json`
- `module-activation-blockers.json`
- `module-mock-runtime-trail.json`
- `module-review-checklist.json`

## Local commands

```bash
./scripts/module-lifecycle-dashboard-check.sh
./scripts/operator-console-static-demo.sh --offline-ok --skip-api
python3 -m http.server 8090 --directory operator-console-static
```

## No-go conditions

- Activation controls are enabled.
- A write method is added.
- Non-local API origins are accepted.
- External calls occur.
- Runtime route registration appears.
- Code loading appears.
- Raw prompts, hidden reasoning, credentials, or protected values render.
- A frontend dependency or build system is added.

## AION-105 Review Gate

AION-105 uses the dashboard as operator-visible evidence for the module
activation design review. The dashboard remains read-only. It may show the
plugin boundary evidence pack, lifecycle traceability matrix, and no-go
regression status, but it must not add activation controls, capability
activation controls, runtime registration controls, code loading controls, or
module write controls.
