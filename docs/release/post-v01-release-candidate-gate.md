# Post-v0.1 Release Candidate Gate

## Purpose

AION-118 creates a post-v0.1 release candidate evidence gate. The gate
consolidates the completed operator platform, connector platform, local auth
review, module activation design review, and AION-117 platform integration
checkpoint into one candidate baseline before v0.2 planning.

This is release-candidate evidence only. It is not a release, does not create a
v0.2 tag, and does not approve runtime implementation.

## Scope

In scope:

- post-v0.1 release candidate evidence
- cross-phase freeze evidence
- release candidate checklist and no-go regression
- implementation approval lock
- v0.2 planning boundary
- static console demo data for the release candidate state
- repository-local release candidate scripts

Out of scope:

- v0.2 implementation
- v0.2 release or tag creation
- connector runtime enablement
- operator write execution
- production auth runtime
- module activation, capability activation, code loading, or runtime registration
- external calls, provider SDKs, connector SDK dependencies, or network clients
- credential storage, token storage, OAuth, OIDC, or SAML runtime
- sandbox execution
- package manager files, lockfiles, frontend dependencies, migrations, API
  runtime execution routes, SDK resource implementations, or CLI command
  implementations

## Required Prior Gates

The release candidate gate requires these prior gates to be present and
passing:

- `./scripts/platform-integration-checkpoint.sh`
- `./scripts/platform-integration-freeze-check.sh`
- `./scripts/platform-integration-no-go-regression.sh`
- `./scripts/operator-platform-regression.sh`
- `./scripts/operator-platform-freeze-gate.sh`
- `./scripts/connector-platform-regression.sh`
- `./scripts/connector-platform-stabilization-gate.sh`
- `./scripts/auth-prototype-review.sh`
- `./scripts/module-activation-design-review.sh`
- `./scripts/ui-release-gate.sh`
- `./scripts/static-console-safety-check.sh`
- `./scripts/docs-check.sh`
- `./scripts/final-docs-audit.sh`
- `./scripts/verify-no-domain-drift.sh`
- `./scripts/boundary-check.sh`

## Operator Platform Evidence

The operator platform evidence proves that the static console remains
read-only, operator action requests remain dry-run descriptors, local auth and
local session previews remain dev-only, role filtering changes visibility only,
and production auth remains unapproved.

The operator evidence remains blocked from write execution, tool execution,
hard deletion, runtime config mutation, production auth, credential storage,
token storage, external identity provider runtime, package files, and
migrations.

## Connector Platform Evidence

The connector platform evidence proves that connector runtime implementation
remains disabled and unapproved. Connector release, safety freeze, checkpoint,
and stabilization evidence remain docs, examples, static demo data, and local
verification scripts only.

The connector evidence remains blocked from runtime execution, external calls,
credential access, token storage, sandbox execution, activation, route
registration, provider SDKs, connector SDK dependencies, package files, and
migrations.

## Platform Integration Evidence

AION-117 ties the operator and connector tracks together through the platform
integration checkpoint, cross-phase evidence pack, future runtime boundary
freeze, implementation approval state summary, and closeout checklist.

AION-118 treats that integration checkpoint as a required input, not as
permission to implement v0.2 runtime features.

## Release Blocker Conditions

The release candidate gate fails if any evidence or changed file creates or
approves:

- a v0.2 tag or v0.2 release
- connector runtime execution
- operator write execution
- production auth runtime
- module activation, capability activation, code loading, or runtime registration
- external calls, external model calls, provider SDKs, network clients, or
  connector SDK dependencies
- credential or token storage
- OAuth, OIDC, or SAML runtime
- sandbox execution
- package manager files, lockfiles, frontend dependencies, or package install
  instructions
- migrations
- runtime API execution routes
- SDK resource implementations or CLI command implementations
- `implementation_approved=true` or any release approval boolean set true
- privileged bypass, policy bypass, or audit bypass
- movement, deletion, or recreation of `aion-v0.1.0`

## Pass/Fail Criteria

The release candidate passes only when all required docs exist, ADR 0109 is
indexed, release examples are valid synthetic JSON, static console data is
bundled and read-only, all implementation approval booleans remain false, no
v0.2 tag exists, `aion-v0.1.0` remains untouched, and all required local gates
pass.

The release candidate fails closed if any no-go check finds runtime
enablement, write execution, external calls, protected material storage,
sandbox execution, package or migration drift, runtime API route drift, SDK/CLI
implementation drift, or release approval drift.

## No v0.2 Tag

AION-118 explicitly creates no v0.2 tag. It does not create a release and does
not mutate the v0.1 release baseline.

## AION-119 Planning Charter Follow-Up

AION-119 uses this release candidate gate as the required baseline for v0.2
planning. The planning charter may describe future ADRs, gates, workstreams,
and backlog intake criteria, but it does not create a v0.2 tag, create a
release, approve runtime implementation, enable external calls, store
credentials or tokens, enable sandbox execution, add package files, or add
migrations.
