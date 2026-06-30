# Operator View Spec

Future Operator Console views must consume existing Brain APIs or CLI
workflows. AION-087 does not add API routes, CLI commands, SDK resources, or a
runtime UI.

| View | Data source | Existing endpoint or CLI command | Display fields | Redacted fields | Allowed actions | Forbidden actions | Operator decision supported |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Overview | Operator Control Tower, health, readiness | `GET /health`, `GET /health/ready`, `./scripts/operator-overview.sh` | status, blockers, queue counts, latest findings | raw prompts, hidden reasoning, secrets | refresh, acknowledge findings | activate modules, bypass policy | Is the local system reviewable? |
| Readiness | setup doctor, bootstrap, readiness checks | `./scripts/setup-doctor.sh --fast --offline-ok` | finding id, severity, status, component | raw headers, secret-like values | run setup doctor, seed local defaults | install packages, create production credentials | What blocks local readiness? |
| Release Candidate | RC matrices and evidence | `./scripts/rc-check.sh --offline-ok` | RC id, gate status, blocker count, evidence refs | raw payloads, hidden reasoning, secrets | run RC gate, dismiss non-blocker with reason | push to main, bypass release gates | Is the candidate reviewable? |
| Freeze/Release | freeze and release package dry-runs | `./scripts/v0.1-final-verify.sh --offline-ok --skip-docker --skip-api` | version, freeze status, package dry-run state | local env values, secrets | run freeze dry-run, run package dry-run | move release tag, publish artifacts | Can release closure proceed? |
| Golden Path | synthetic scenario harness | `./scripts/golden-path.sh --offline-ok` | scenario id, status, trace refs, findings | raw prompts, provider payloads | run Golden Path | add domain scenario packs | Does core deterministic flow work? |
| Module Lifecycle | extension, slot, binding, conformance, readiness | `./scripts/module-pack-check.sh` | module key, lifecycle state, blockers, readiness score | suspicious manifest fields, secrets | validate manifest, run dry-runs | load code, install package | What blocks module readiness? |
| Module Activation | activation request and gate | `./scripts/generic-knowledge-demo.sh --offline-ok --skip-api` | request id, activation_allowed, blockers | raw manifest payloads, secrets | run activation gate dry-run | activate module, activate capability | Why is activation blocked? |
| Module Mock Runtime | mock profile and synthetic invocation | `./scripts/generic-knowledge-demo.sh --offline-ok --skip-api` | mock run id, synthetic output flag, execution flags | raw untrusted input | run module mock invocation | execute package code, call tools | Does dry-run output stay synthetic? |
| Model Provider Hardening | provider profile, egress preview, simulation, readiness | `./scripts/model-provider-check.sh --offline-ok --skip-api` | provider key, egress allowed, external_call_ready, blockers | raw prompts, credentials, provider payloads | run egress preview, run simulation | enable external calls, store credentials | Is provider posture safe for review? |
| Notifications | notification ledger | `./scripts/aionctl.sh --scope workspace:main notifications alerts` | notification id, severity, status, topic | raw headers, secrets | acknowledge notification | send external notification | What needs operator attention? |
| Incidents | incident correlation and root-cause candidates | `./scripts/aionctl.sh --scope workspace:main incidents list` | incident id, status, candidate refs, recovery state | hidden reasoning, secrets | create recovery review record | auto-remediate, mutate source | What happened and what review remains? |
| Registry Integrity | resource registry and link validation | `./scripts/aionctl.sh --scope workspace:main resources validate` | resource id, URI, link status, owner scope | secret-like URI parameters | run validation | repair links automatically | Are references coherent? |
| Lifecycle Review | retention and purge preview | `./scripts/aionctl.sh --scope workspace:main lifecycle evaluate` | candidate id, retention class, preview status | secret-like values | run lifecycle evaluation, run purge preview | hard delete records | What can be reviewed safely? |
| Audit/Provenance | audit ledger and provenance hashes | `./scripts/audit-verify.sh` | audit id, hash, actor, timestamp, refs | raw prompts, hidden reasoning, raw headers, secrets | verify audit integrity | alter audit history | Is evidence traceable? |
| Settings Safety | runtime config and feature flags | `./scripts/config-validate.sh` | feature key, default, override status, risk | env values, credentials | validate config snapshot | mutate production config | Are unsafe toggles disabled? |

## AION-088 view model path

The view spec now has a read-only API contract:
`POST /brain/operator-console/view-model`. This endpoint returns redacted
sections, data sources, descriptor-only actions, forbidden action descriptors,
and refs.

It adds no runtime UI, no frontend state, no activation, and no execution. It
must preserve no raw prompt exposure, no hidden reasoning exposure, and no
secret exposure.

## AION-089 static prototype path

The static prototype consumes the same view names and data shape from
`POST /brain/operator-console/view-model` when the local API is reachable. It
does not add routes or contracts. Offline mode renders synthetic JSON examples
from `operator-console-static/demo-data/`.

The static prototype includes these sections:

- Overview
- Readiness
- Release Candidate
- Module Lifecycle
- Model Provider Hardening
- Incidents
- Registry and Lifecycle
- Settings Safety
- Audit and Provenance

All action entries remain descriptors. Buttons are disabled and are not wired
to mutation endpoints.

## AION-090 module dashboard path

The static Module Lifecycle dashboard reuses the Module Lifecycle view and adds
local JSON for the Generic Knowledge Intelligence trail. It shows:

- Manifest
- Intake
- Slot
- Bindings
- Validation
- Conformance
- Readiness
- Activation Request
- Activation Gate
- Mock Runtime
- Operator Review

Safety labels must remain visible:

- `activation_allowed=false`
- `execution_allowed=false`
- `registration_allowed=false`
- `code_loaded=false`
- `external_calls_made=false`

The dashboard adds no new API route and no write action.

## AION-092 operator action view

The Operator Actions view shows dry-run request metadata, expected effects,
blocked effects, blockers, review decisions, and safety flags. It must render
`execution_allowed=false`, `external_calls_allowed=false`,
`activation_allowed=false`, and `would_execute=false`.

## AION-094 local auth view

The static console includes a Local Auth Status panel showing
`production_auth_enabled=false`, `credentials_enabled=false`,
`sessions_enabled=false`, `external_identity_provider_enabled=false`, and
`write_actions_enabled=false`. The role filter demo is read-only and redacted.

## Local Session Preview Section

Operator view models may include or be filtered by local session preview
metadata. The section must render read-only status and boundary flags only:
dev-only, read-only, production-session disabled, auth material disabled,
browser-state disabled, persistence disabled, writes disabled, execution
disabled, activation disabled, and external calls disabled.

## AION-096 Role Filter Metadata

View models may include role-filter metadata such as removed sections, removed
actions, visible forbidden descriptors, and role matrix version. The response
shape remains read-only and redacted.

## AION-097 Action Authorization Metadata

View models may advertise `dry_run_action_authz_supported=true` as a read-only
capability note. This indicates preview/review authorization evidence is
available, not that execution, activation, writes, or external calls are
available.

## AION-099 Auth Runtime Metadata

Static console demo data may include disabled auth runtime status and mock
claims preview metadata. Required false flags include production auth, auth
runtime enablement, external identity provider, credentials, token issuance,
cookie issuance, session persistence, login endpoint, and logout endpoint. Mock
claims preview metadata is synthetic and must not imply authentication,
execution authorization, activation authorization, or production identity.

## AION-100 UI Release Gate Metadata

Static console metadata may include UI release gate evidence from
`examples/operator-console/ui-release-gate-result.json`,
`examples/operator-console/ui-safety-matrix.json`, and
`examples/operator-console/static-console-artifact-manifest.json`. This evidence
is release-check metadata only and must not add UI runtime state, write
controls, auth runtime enablement, provider calls, activation, execution, or
frontend dependencies.

## AION-103 Static UX Metadata

Static console metadata may include navigation and accessibility evidence from
`examples/operator-console/static-console-navigation-map.json` and
`examples/operator-console/static-console-accessibility-check-result.json`.
This metadata describes group membership, section shortcuts, safe local command
copy, and accessibility checks only. It must not add UI runtime state, write
controls, auth runtime enablement, provider calls, activation, execution,
external calls, browser storage, or frontend dependencies.

## AION-111 Connector Policy Preview

The static connector panel includes connector policy catalog and dry-run demo
data. It displays false runtime, external call, credential, token, activation,
route, tool, and write indicators. It has no connector form and no runtime
control.
