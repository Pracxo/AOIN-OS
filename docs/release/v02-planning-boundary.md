# v0.2 Planning Boundary

## Purpose

This boundary allows future v0.2 planning to begin from the frozen post-v0.1
release candidate baseline without approving runtime implementation.

## v0.2 Planning Allowed Areas

Future planning may describe:

- scoped ADR candidates for connector runtime implementation
- scoped ADR candidates for operator write execution
- scoped ADR candidates for production auth
- scoped ADR candidates for module activation
- staged release gates and rollback criteria
- safety invariants that must stay false until implementation is approved
- test plans, evidence packs, and no-go regression requirements

## v0.2 Implementation Not Approved Yet

The following remain unapproved:

- connector runtime implementation
- operator write execution
- production auth runtime
- module activation, capability activation, code loading, and runtime registration
- external calls and external model calls
- credential storage and token storage
- OAuth, OIDC, and SAML runtime
- sandbox execution
- runtime API execution routes
- SDK resource implementations and CLI command implementations
- package files, lockfiles, frontend dependencies, and migrations

## Required ADRs Before Implementation

Future implementation requires explicit ADRs for the exact scope being changed.
Each ADR must state the allowed behavior, denied behavior, required gates,
rollback model, audit model, and no-go regression.

## Required Gates Before Implementation

Implementation cannot begin until a future task adds and passes the relevant
implementation gate, no-go regression, docs evidence, example evidence, static
console evidence if applicable, focused tests, boundary checks, and full
repository checks.

## Blocked Work Types

Blocked work includes creating a v0.2 tag, creating a release, enabling runtime
execution, registering runtime routes, adding network clients, adding provider
or connector SDK dependencies, storing protected material, executing sandboxed
code, adding migrations, adding package manager files, or pushing directly to
main.

## No-Go Conditions

Planning fails closed if it changes an approval boolean to true, adds runtime
implementation, adds external call paths, stores credentials or tokens, enables
sandbox execution, adds package or migration drift, creates a v0.2 tag, or
mutates `aion-v0.1.0`.

## AION-119 Planning Charter

AION-119 formalizes this boundary with the v0.2 planning charter, runtime
implementation decision framework, candidate workstream map, ADR requirements,
gate dependency matrix, backlog intake criteria, and planning no-go regression.
The boundary remains planning-only and implementation-unapproved.
