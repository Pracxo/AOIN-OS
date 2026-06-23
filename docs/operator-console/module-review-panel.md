# Module Review Panel

## Review checklist

The static Module Review panel renders a checklist for:

- manifest valid
- no executable payload
- no external source
- no dynamic route
- no full autonomy
- bindings validated
- conformance dry-run passed
- readiness created
- activation blocked
- mock runtime synthetic
- audit/provenance expected

## What an operator may approve

An operator may approve the evidence as understandable and safe for review.
That approval can mean the metadata shape, refs, blockers, and synthetic
outputs are coherent.

## What remains blocked

The following remain blocked:

- module activation
- capability activation
- code loading
- runtime registration
- dynamic route registration
- package installation
- external calls
- provider calls
- controlled execution
- tool execution
- runtime config mutation

## Why approval is not activation

Review approval is an interpretation of evidence. Activation would require a
runtime state change, policy decision, approval semantics, sandbox boundary,
rollback path, disable path, release gate, and audit/provenance coverage. None
of those are enabled by the static dashboard.

## Required future activation gates

Future activation requires a separate task with:

- activation request semantics
- policy and permission coverage
- approval and autonomy constraints
- sandbox execution design
- runtime adapter boundary
- rollback and disable design
- conformance and readiness evidence
- operator acceptance
- release gate coverage
