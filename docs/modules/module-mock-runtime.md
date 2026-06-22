# Deterministic Module Mock Runtime

AION-085 adds a deterministic module mock runtime for post-v0.1 module
readiness. It is a backend metadata layer that records safe dry-run module
invocation evidence before any future activation path can be considered.

The runtime owns:

- mock profiles
- dry-run invocation requests
- synthetic outputs
- run records
- reviewable findings
- aggregate queries

It does not load code, install packages, activate modules, invoke real
capabilities, register routes, mutate runtime configuration, execute shell
commands, call external services, or implement domain-specific module logic.

## Records

`ModuleMockProfile` describes deterministic simulation rules and schema hints.
Profiles are metadata only.

`ModuleMockInvocationRequest` stores the redacted input, expected output shape,
scope, policy references, sandbox references, and payload hash for one dry-run.

`ModuleMockRun` stores the result. All runtime execution flags must remain:

- `activation_allowed=false`
- `execution_allowed=false`
- `external_calls_made=false`
- `code_loaded=false`

`ModuleMockOutput` stores synthetic output only. It must include
`synthetic=true`.

`ModuleMockFinding` stores reviewable metadata problems such as missing
bindings, invalid shapes, unsafe input, missing mock profiles, or executable
runtime references.

## API

- `POST /brain/module-mock/profiles`
- `POST /brain/module-mock/profiles/seed-defaults`
- `GET /brain/module-mock/profiles`
- `GET /brain/module-mock/profiles/{mock_profile_id}`
- `POST /brain/module-mock/invoke`
- `GET /brain/module-mock/runs`
- `GET /brain/module-mock/runs/{module_mock_run_id}`
- `GET /brain/module-mock/outputs`
- `GET /brain/module-mock/outputs/{module_mock_output_id}`
- `GET /brain/module-mock/findings`
- `POST /brain/module-mock/findings/{module_mock_finding_id}/dismiss`
- `POST /brain/module-mock/query`

`/brain/module-mock-runtime/*` remains a compatibility alias.

## SDK And CLI

The Python SDK exposes `client.module_mock_runtime`.

The CLI exposes:

```bash
./scripts/aionctl.sh --scope workspace:main module-mock seed-profiles
./scripts/aionctl.sh --scope workspace:main module-mock invoke <binding-id> --capability-key generic.example
./scripts/aionctl.sh --scope workspace:main module-mock runs
./scripts/aionctl.sh --scope workspace:main module-mock outputs
./scripts/aionctl.sh --scope workspace:main module-mock findings
./scripts/aionctl.sh --scope workspace:main module-mock query
```

## Release And Operator Integration

The runtime contributes read-only evidence to:

- module activation gate summaries
- conformance when explicitly requested by metadata
- resource registry descriptors
- release package summaries
- freeze gate checks
- security hardening checks
- operator status cards, queues, and action items

The safety boundary is explicit: no code loading, no package installation, no
external calls, no activation, and no capability execution.

These integrations read records only. They do not enable activation or
execution.
