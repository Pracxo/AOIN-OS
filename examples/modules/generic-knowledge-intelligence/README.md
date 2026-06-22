# Generic Knowledge Intelligence Module Pack

This directory contains the first post-v0.1 governed module package for AION OS.
It is metadata only. It proves the module ecosystem path without loading code,
installing packages, registering routes, activating capabilities, or executing
runtime logic.

## Purpose

Generic Knowledge Intelligence is a dry-run module pack for generic knowledge
retrieval, summary, grounding, explanation, and answer contracts. The pack
exercises the existing gates:

manifest -> intake -> module slot -> capability binding -> binding validation
-> conformance -> readiness -> activation request -> activation gate -> blocker
review -> runtime registration preview -> operator review

## Safety Boundaries

- No executable payload is present.
- No routes are declared.
- No external dependencies are declared.
- No external source is declared.
- No package installation is requested.
- No runtime registration is requested.
- No code loading is requested.
- No controlled mode is supported.
- No tool execution is requested.
- No full autonomy is requested.
- Activation blockers are expected in v0.1.

## Fixtures

- `manifest.json`: extension manifest for `generic.knowledge_intelligence`
- `intake-request.json`: dry-run extension intake request
- `module-slot-request.json`: inactive module slot create request
- `capability-bindings.json`: five inactive capability binding requests
- `binding-validation-request.json`: dry-run binding validation request
- `conformance-profile.json`: generic conformance profile request
- `test-vectors.json`: synthetic schema-only and mock-input vectors
- `conformance-run-request.json`: dry-run conformance run request
- `readiness-assessment-request.json`: readiness assessment request
- `activation-request.json`: future activation request with expected false gates
- `activation-gate-request.json`: gate request plus expected blocker assertions
- `operator-review-request.json`: review record that does not activate anything

## Dry-Run Sequence

From the repository root:

```bash
./scripts/module-pack-check.sh
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
```

When the Brain API is running locally, the demo can validate the manifest and
run safe dry-run API steps:

```bash
./scripts/generic-knowledge-demo.sh --offline-ok --api-url http://localhost:8080
```

The script rejects non-local API URLs and never runs controlled mode.

## Expected Blockers

The activation gate must keep activation blocked. Expected blocker categories
are:

- `activation_disabled`
- `runtime_registration_disabled`
- `dynamic_route_registration_disabled`
- `code_loading_disabled`

The readiness trail expects `activation_ready=false`.

## No-Go Conditions

Stop the module pack review if any fixture introduces executable payloads,
external dependencies, source URLs, route registration, runtime registration,
capability activation, raw secret access, external model calls, tool execution,
full autonomy, or domain workflow logic.

## Ecosystem Proof

This pack demonstrates that AION can move a candidate module through the
post-v0.1 governance path as records and evidence only. The result is an
operator-readable readiness trail, not an active module.
