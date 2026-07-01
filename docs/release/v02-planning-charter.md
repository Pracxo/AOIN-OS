# v0.2 Planning Charter

## Purpose

AION-119 defines the planning charter for v0.2 work after the post-v0.1 release
candidate gate. It gives future implementation proposals a governed entry point
without approving or implementing runtime capabilities.

## Scope

In scope:

- v0.2 planning goals
- candidate runtime implementation workstreams
- required ADRs before implementation
- required gate and evidence dependencies
- backlog intake criteria
- no-go planning boundary
- static console planning evidence
- repository-local planning checks

Out of scope:

- v0.2 implementation
- v0.2 release or tag creation
- connector runtime enablement
- operator write execution
- production auth runtime
- module activation, capability activation, code loading, or runtime registration
- external calls, external notifications, external model calls, network clients,
  provider SDKs, or connector SDK dependencies
- credential storage, token storage, OAuth, OIDC, or SAML runtime
- sandbox execution
- package files, lockfiles, frontend dependencies, migrations, API runtime
  execution routes, SDK resource implementations, or CLI command implementations

## v0.2 Planning Goals

Planning may define the problem statements, risks, ADR dependencies, gate
dependencies, rollout sequence, audit/provenance requirements, rollback model,
operator review model, and no-go checks needed for future implementation.

Planning may also map workstreams to prerequisites and identify blockers. It
must not change approval state or add runtime paths.

## Out-of-Scope Runtime Implementation

AION-119 does not approve runtime implementation. All runtime implementation
approval booleans remain false, and all runtime execution surfaces remain
disabled or absent.

## Required Decision Gates

Future implementation proposals must pass the relevant existing gates first:

- `./scripts/post-v01-release-candidate-gate.sh`
- `./scripts/post-v01-release-candidate-freeze.sh`
- `./scripts/post-v01-release-candidate-no-go-regression.sh`
- `./scripts/platform-integration-checkpoint.sh`
- `./scripts/platform-integration-freeze-check.sh`
- `./scripts/platform-integration-no-go-regression.sh`
- `./scripts/v02-planning-charter-check.sh`
- `./scripts/v02-planning-no-go-regression.sh`

Future implementation work must add scoped gates before any approval state can
change.

## Required ADRs

Implementation requires explicit ADRs for the exact workstream. Each ADR must
name the allowed behavior, blocked behavior, approval state change, migration
posture, rollback path, audit/provenance model, operator review model, policy
enforcement model, and no-go regression.

## Required Evidence

Required evidence includes:

- approved ADR for the specific workstream
- pre-implementation gate evidence
- no-go regression evidence
- audit/provenance and rollback evidence
- operator review evidence
- security review evidence
- full repository check evidence
- confirmation that `aion-v0.1.0` remains untouched
- confirmation that no v0.2 tag or release is created before release approval

## Release Blocker Conditions

Planning fails closed if it creates or approves a v0.2 tag or release, approves
runtime implementation, enables production auth, enables connector runtime,
enables operator write execution, enables module activation, enables external
calls, stores credentials or tokens, enables sandbox execution, adds package
files, adds migrations, adds runtime API execution routes, or bypasses policy,
approval, audit, or operator review.

## Planning Exit Criteria

The planning charter passes only when all planning docs exist, ADR 0110 is
indexed, planning examples are valid synthetic JSON, static console planning
data is bundled and read-only, all implementation approval booleans remain
false, no v0.2 tag or release exists, `aion-v0.1.0` remains untouched, and all
planning gates pass.

## No v0.2 Tag

AION-119 explicitly creates no v0.2 tag. It creates no release and does not
mutate the v0.1 release baseline.

## AION-120 Stabilization

AION-120 stabilizes this charter with a planning stabilization gate, backlog
governance freeze, implementation readiness scorecard, decision review
calendar, blocked work register, and planning no-go stabilization checks.
The stabilization layer does not approve implementation, create a v0.2 tag,
create a release, or change any runtime boundary.

## AION-121 Readiness Final Review

AION-121 closes this charter for planning review purposes only with a final
readiness review, closeout report, implementation approval guard, evidence
matrix, blocked implementation summary, final no-go review, and final
checklist. The final review does not approve implementation, create a v0.2 tag,
create a release, or change any runtime boundary.
