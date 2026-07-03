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

AION-111 adds connector policy catalog and dry-run preview data:

- `demo-data/connector-policy-catalog.json`
- `demo-data/connector-policy-dry-run.json`

The panel remains static and informational. It has no connector allow control,
no enable control, no call control, no credential input, no token input, and no
runtime activation path.

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

## AION-113 Connector Credential Panels

The static console includes connector credential boundary, readiness, and
redaction preview panels. The panels load bundled JSON only, contain no
credential/token/password/key/OAuth inputs, and expose no
store/read/rotate/revoke/login/connect/call controls.

## AION-114 Connector Release Gate Panels

The static console includes connector release gate and safety freeze panels.
They load bundled JSON only, keep implementation approval false, and expose no
runtime, external-call, credential/token, sandbox execution, activation, route
registration, input, or write controls.

## AION-115 Connector Platform Checkpoint Panels

The static console includes connector platform checkpoint and phase closeout
panels. They load bundled JSON only, keep connector implementation unapproved,
and expose no runtime, external-call, credential/token, sandbox execution,
activation, route registration, input, package, migration, or write controls.

## AION-116 Connector Platform Stabilization Panels

The static console includes connector platform stabilization and phase freeze
gate panels. They load bundled JSON only, keep connector implementation
unapproved, and expose no runtime, external-call, credential/token, sandbox
execution, activation, route registration, input, package, migration, or write
controls.

Validate the stabilization evidence:

```bash
./scripts/connector-platform-regression.sh
./scripts/connector-platform-stabilization-gate.sh
```

## AION-117 Platform Integration Checkpoint Panels

The static console includes post-v0.1 platform integration checkpoint and
future runtime boundary freeze panels. They load bundled JSON only, keep
operator write execution, connector implementation, production auth, module
activation, external calls, credential storage, token storage, and sandbox
execution unapproved, and expose no input, package, migration, runtime, or
write controls.

Validate the integration evidence:

```bash
./scripts/platform-integration-checkpoint.sh
./scripts/platform-integration-freeze-check.sh
./scripts/platform-integration-no-go-regression.sh
```

## AION-118 Release Candidate Panels

The static console includes post-v0.1 release candidate and v0.2 planning
boundary panels. They load bundled JSON only, keep operator write execution,
connector implementation, production auth, module activation, external calls,
credential storage, token storage, sandbox execution, v0.2 release approval,
and v0.2 tag creation unapproved or false, and expose no input, package,
migration, runtime, release, or write controls.

Validate the release candidate evidence:

```bash
./scripts/post-v01-release-candidate-gate.sh
./scripts/post-v01-release-candidate-freeze.sh
./scripts/post-v01-release-candidate-no-go-regression.sh
```

## AION-119 v0.2 Planning Panels

The static console includes v0.2 planning charter and gate dependency matrix
panels. They load bundled JSON only, keep runtime implementation, operator
write execution, connector implementation, production auth, module activation,
external calls, credential storage, token storage, sandbox execution, v0.2
release creation, and v0.2 tag creation unapproved or false, and expose no
input, package, migration, runtime, release, or write controls.

Validate the v0.2 planning evidence:

```bash
./scripts/v02-planning-charter-check.sh
./scripts/v02-planning-no-go-regression.sh
```

## AION-120 v0.2 Planning Stabilization Panels

The static console includes v0.2 planning stabilization and implementation
readiness scorecard panels. They load bundled JSON only, keep runtime
implementation, backlog implementation approval, operator write execution,
connector implementation, production auth, module activation, external calls,
credential storage, token storage, sandbox execution, v0.2 release creation,
and v0.2 tag creation unapproved or false, and expose no input, package,
migration, runtime, release, or write controls.

Validate the v0.2 planning stabilization evidence:

```bash
./scripts/v02-planning-stabilization-gate.sh
./scripts/v02-planning-freeze-check.sh
./scripts/v02-planning-stabilization-no-go-regression.sh
```

## AION-121 v0.2 Readiness Final Review Panels

The static console includes v0.2 readiness final review and implementation
approval guard panels. They load bundled JSON only, keep runtime
implementation, backlog implementation approval, operator write execution,
connector implementation, production auth, module activation, external calls,
credential storage, token storage, sandbox execution, v0.2 release creation,
and v0.2 tag creation unapproved or false, and expose no input, package,
migration, runtime, release, tag, approval, or write controls.

Validate the v0.2 readiness final evidence:

```bash
./scripts/v02-readiness-final-review.sh
./scripts/v02-readiness-final-freeze.sh
./scripts/v02-readiness-final-no-go-regression.sh
```

## AION-122 v0.2 Implementation Kickoff Panels

The static console includes v0.2 implementation kickoff boundary and runtime
workstream lock panels. They load bundled JSON only, keep runtime
implementation, backlog implementation approval, approval workflow bypass, ADR
dependency bypass, gate dependency bypass, operator write execution, connector
implementation, production auth, module activation, external calls, credential
storage, token storage, sandbox execution, v0.2 release creation, and v0.2 tag
creation unapproved or false, and expose no input, package, migration,
runtime, release, tag, approval, bypass, or write controls.

Validate the v0.2 implementation kickoff evidence:

```bash
./scripts/v02-implementation-kickoff-boundary-check.sh
./scripts/v02-implementation-kickoff-freeze.sh
./scripts/v02-implementation-kickoff-no-go-regression.sh
```

## AION-123 v0.2 Approval Workflow Panels

The static console includes v0.2 approval workflow stabilization and
implementation request intake panels. They load bundled JSON only, keep runtime
implementation, backlog implementation approval, approval workflow bypass, ADR
dependency bypass, gate dependency bypass, approval expiry bypass, approval
revocation bypass, dual-control bypass, operator write execution, connector
implementation, production auth, module activation, external calls, credential
storage, token storage, sandbox execution, v0.2 release creation, and v0.2 tag
creation unapproved or false, and expose no input, package, migration,
runtime, release, tag, approval, bypass, or write controls.

Validate the v0.2 approval workflow evidence:

```bash
./scripts/v02-approval-workflow-stabilization-gate.sh
./scripts/v02-approval-workflow-freeze.sh
./scripts/v02-approval-workflow-no-go-regression.sh
```

## AION-124 v0.2 Workstream Intake Panels

The static console includes v0.2 workstream intake readiness and implementation
sequencing freeze panels. They load bundled JSON only, keep runtime
implementation, backlog implementation approval, workstream implementation
approval, approval workflow bypass, approval record missing, ADR dependency
bypass, gate dependency bypass, approval expiry bypass, approval revocation
bypass, dual-control bypass, operator write execution, connector
implementation, production auth, module activation, external calls, credential
storage, token storage, sandbox execution, v0.2 release creation, and v0.2 tag
creation unapproved or false, and expose no input, package, migration,
runtime, release, tag, approval, bypass, or write controls.

Validate the v0.2 workstream intake evidence:

```bash
./scripts/v02-workstream-intake-readiness-gate.sh
./scripts/v02-workstream-intake-freeze.sh
./scripts/v02-workstream-intake-no-go-regression.sh
```

## AION-125 v0.2 Pre-Implementation Master Freeze Panels

The static console includes v0.2 pre-implementation master freeze and final
planning baseline panels. They load bundled JSON only, keep runtime
implementation, backlog implementation approval, workstream implementation
approval, approval workflow bypass, approval record missing, ADR dependency
bypass, gate dependency bypass, approval expiry bypass, approval revocation
bypass, dual-control bypass, operator write execution, connector
implementation, production auth, module activation, external calls, credential
storage, token storage, sandbox execution, v0.2 release creation, and v0.2 tag
creation unapproved or false, and expose no input, package, migration,
runtime, release, tag, approval, bypass, or write controls.

Validate the v0.2 pre-implementation master freeze evidence:

```bash
./scripts/v02-preimplementation-master-freeze.sh
./scripts/v02-preimplementation-final-baseline-check.sh
./scripts/v02-preimplementation-master-no-go-regression.sh
```

## AION-126 v0.2 Workstream Proposal Registry Panels

The static console includes v0.2 workstream proposal registry and approval
queue preview panels. They load bundled JSON only, keep the proposal registry
preview-only, keep the approval queue preview-only, keep approval queue item
approval false, keep runtime implementation, backlog implementation approval,
workstream implementation approval, approval workflow bypass, approval record
missing, ADR dependency bypass, gate dependency bypass, operator write
execution, connector implementation, production auth, module activation,
external calls, credential storage, token storage, sandbox execution, v0.2
release creation, and v0.2 tag creation unapproved or false, and expose no
input, package, migration, runtime, release, tag, approval, bypass, or write
controls.

Validate the v0.2 proposal registry evidence:

```bash
./scripts/v02-workstream-proposal-registry-check.sh
./scripts/v02-proposal-registry-freeze.sh
./scripts/v02-proposal-registry-no-go-regression.sh
```

## AION-127 v0.2 Proposal Registry Stabilization Panels

The static console includes v0.2 proposal registry stabilization and approval
queue freeze panels. They load bundled JSON only, keep the proposal registry
preview-only, keep the approval queue preview-only, keep approval queue item
approval false, keep proposal implementation approval false, keep runtime
implementation approval false, keep backlog and workstream implementation
approval false, keep approval workflow bypass, approval record missing, ADR
dependency bypass, gate dependency bypass, approval expiry bypass, approval
revocation bypass, and dual-control bypass false, and keep external calls,
credential storage, token storage, sandbox execution, v0.2 release creation,
and v0.2 tag creation unapproved or false. They expose no input, package,
migration, runtime, release, tag, approval, bypass, or write controls.

Validate the v0.2 proposal registry stabilization evidence:

```bash
./scripts/v02-proposal-registry-stabilization-gate.sh
./scripts/v02-approval-queue-freeze.sh
./scripts/v02-approval-queue-no-go-regression.sh
```

## AION-128 v0.2 Planning Master Checkpoint Panels

The static console includes v0.2 planning master checkpoint and implementation
lock freeze panels. They load bundled JSON only, keep the proposal registry
preview-only, keep the approval queue preview-only, keep approval queue item
approval false, keep proposal implementation approval false, keep runtime,
backlog, and workstream implementation approval false, keep approval workflow
bypass, approval record missing, ADR dependency bypass, and gate dependency
bypass false, and keep external calls, credential storage, token storage,
sandbox execution, v0.2 release creation, and v0.2 tag creation unapproved or
false. They expose no input, package, migration, runtime, release, tag,
approval, bypass, or write controls.

Validate the v0.2 planning master checkpoint evidence:

```bash
./scripts/v02-planning-master-checkpoint.sh
./scripts/v02-planning-master-freeze.sh
./scripts/v02-planning-master-no-go-regression.sh
```
