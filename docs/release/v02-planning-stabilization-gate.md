# v0.2 Planning Stabilization Gate

## Purpose

AION-120 stabilizes the v0.2 planning charter from AION-119 before any
implementation task can be accepted. The gate freezes the planning and backlog
governance boundary while keeping all runtime implementation approvals false.

## Scope

In scope:

- planning stabilization evidence
- backlog governance freeze evidence
- ADR dependency evidence
- gate dependency evidence
- implementation readiness scoring
- blocked work registration
- planning no-go regression checks
- static read-only console planning evidence

Out of scope:

- v0.2 implementation
- v0.2 tag or release creation
- connector runtime enablement
- operator write execution
- production auth
- module activation, capability activation, code loading, or runtime registration
- external calls, network clients, provider SDKs, or connector SDK dependencies
- credential storage, token storage, OAuth, OIDC, or SAML runtime
- sandbox execution
- package files, lockfiles, migrations, API runtime execution routes, SDK
  resources, CLI command implementations, runtime config defaults, or domain
  module logic

## Required Prior Gates

The stabilization gate requires the following prior checks to pass:

- `./scripts/v02-planning-charter-check.sh`
- `./scripts/v02-planning-no-go-regression.sh`
- `./scripts/post-v01-release-candidate-gate.sh`
- `./scripts/post-v01-release-candidate-freeze.sh`
- `./scripts/platform-integration-checkpoint.sh`
- `./scripts/platform-integration-freeze-check.sh`
- `./scripts/docs-check.sh`
- `./scripts/final-docs-audit.sh`
- `./scripts/verify-no-domain-drift.sh`
- `./scripts/boundary-check.sh`

## Planning Charter Evidence

The gate depends on the AION-119 planning charter, runtime decision framework,
candidate workstream map, ADR requirements, gate dependency matrix, backlog
intake criteria, no-go planning boundary, and planning closeout checklist.

## Backlog Governance Evidence

Backlog evidence must show that every v0.2 backlog item is planning-only,
has an ADR mapping, has a gate mapping, names a rollback and audit posture,
and keeps `backlog_implementation_items_approved=false`.

## ADR Dependency Evidence

ADR 0111 records that AION-120 adds a planning stabilization gate and that
future implementation requires explicit scoped ADRs before any approval state
can change.

## Gate Dependency Evidence

Each candidate workstream remains blocked until a scoped implementation gate,
scoped no-go regression, audit/provenance evidence, rollback evidence, security
review, and operator review are present.

## Implementation Approval Lock Checks

The gate fails if any implementation approval is true:

- `runtime_implementation_approved`
- `operator_write_execution_approved`
- `connector_implementation_approved`
- `production_auth_approved`
- `module_activation_approved`
- `external_calls_approved`
- `credential_storage_approved`
- `token_storage_approved`
- `sandbox_execution_approved`
- `backlog_implementation_items_approved`

## Release Blocker Conditions

Release blockers include v0.2 tag creation, v0.2 release creation, runtime
implementation approval, production auth enablement, connector runtime
enablement, operator write execution enablement, module activation, external
calls, credential or token storage, sandbox execution, package files,
migrations, runtime API execution routes, backlog implementation approval,
or any privileged bypass.

## Pass/Fail Criteria

Pass requires all AION-120 docs, examples, static console data, scripts, and
ADR index entries to exist; all examples to be valid synthetic JSON; all
approval booleans to remain false; `aion-v0.1.0` to remain untouched; no v0.2
tag or release to exist; and all required checks to pass.

Fail occurs on missing evidence, unsafe booleans, runtime drift, external
call paths, protected-material storage, sandbox execution, package or migration
drift, or release/tag drift.

## No v0.2 Tag Or Release

AION-120 explicitly creates no v0.2 tag and no release. It does not mutate the
v0.1 release baseline.
