# 0074: Module Activation Request Gate

## Status

Accepted.

## Context

AION Brain v0.1 has metadata-only extension intake, module slots, capability
bindings, conformance, readiness, policy, audit, operator review, and release
gates. Future module activation needs an explicit request and blocker layer
before runtime activation can be designed safely.

## Decision

Add a metadata-only Module Activation Request Gate.

The gate creates AION-owned contracts and records for activation requests,
deterministic gate runs, blockers, reviews, non-executable plans, and runtime
registration previews.

Activation, execution, runtime route registration, code loading, package
installation, runtime configuration mutation, external calls, and domain module
logic remain disabled.

## Reason

AION needs a durable activation evaluation trail before any runtime activation
implementation exists. The gate lets operators and tests see blockers,
required evidence, policy requirements, and previewed runtime shape without
granting activation authority.

## Consequences

Future activation work must consume these records and pass policy, readiness,
operator review, sandbox, audit, provenance, and release gates before it can
mutate runtime behavior.

The current system can answer whether a module is blocked and why, but it
cannot activate that module.

## Constraints

- `activation_allowed` must remain false.
- `execution_allowed` must remain false.
- `registration_allowed` must remain false.
- Runtime registration previews must not register routes.
- Activation plans must be non-executable.
- Open blockers must surface to operator review.
- Public contracts remain independent of runtime-specific clients.
- No domain-specific module logic is introduced.
