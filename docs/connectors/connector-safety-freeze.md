# Connector Safety Freeze

## Frozen Safe State

AION-114 freezes the current connector safe state as release evidence:
connector runtime is disabled, external calls are absent, credentials and tokens
are absent, sandbox execution is absent, activation is absent, and route
registration is absent.

## What Remains Disabled

- connector runtime execution
- external calls and network clients
- provider SDK access
- credential storage and token storage
- OAuth, OIDC, and SAML runtime
- connector sandbox execution
- filesystem, network, process, dynamic import, and install capabilities
- connector activation and route registration
- tool execution, write paths, and hard delete flows

## What Remains Preview-Only

- connector runtime status
- connector policy catalog and dry-run decisions
- connector sandbox readiness
- connector credential readiness
- operator static console connector panels
- SDK and CLI preview commands from earlier connector milestones

## What Remains Synthetic-Only

- connector dry-run simulator output
- connector release evidence examples
- static console demo data
- release gate and safety freeze result examples

## What Must Not Change Without A New ADR

Connector implementation must not begin without a new ADR that explicitly
approves runtime behavior, external-call handling, production auth dependency,
credential store implementation, sandbox implementation, rollback design, audit
design, and release-gate evidence.

## Release Freeze Decision

The connector platform is safe to keep in the post-v0.1 release line only as a
disabled, preview-only, synthetic-evidence surface. AION-114 does not approve
connector implementation.

## Rollback Path

If a future connector change violates this freeze, rollback is to remove the
runtime enablement, remove the unsafe artifact, rerun `./scripts/connector-
release-gate.sh`, rerun `./scripts/connector-safety-freeze.sh`, and keep the
v0.1 release tag untouched.

## Evidence Requirements

Evidence requires the connector release gate result, safety freeze result,
end-to-end readiness pack, release evidence matrix, implementation readiness
decision, ADR 0105, and green no-go regressions.

## AION-115 Checkpoint Input

The safety freeze is a prerequisite for the connector platform checkpoint and
platform freeze check. AION-115 preserves the frozen safe state and does not
move, delete, or recreate the v0.1 release tag.
