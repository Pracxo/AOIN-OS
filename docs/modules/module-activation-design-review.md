# Module Activation Design Review

## Purpose

AION-105 reviews the post-v0.1 module and plugin activation design before any
future implementation work can attempt activation. The review freezes the
current disabled state, collects evidence for every existing module lifecycle
gate, and adds a pre-gate for later architecture tasks.

This is a review artifact only. It does not enable module activation, capability
activation, runtime registration, code loading, package installation,
controlled execution, or plugin execution.

## Scope Reviewed

The review covers the existing module lifecycle:

- extension manifest validation
- extension intake
- module slot staging
- capability binding registry
- binding validation
- conformance
- readiness assessment
- activation request records
- activation gate blockers
- runtime registration preview
- module mock runtime
- operator review
- release and freeze checks
- boundary checks

The review also covers the first governed module trail for Generic Knowledge
Intelligence and the read-only Operator Console module lifecycle dashboard.

## Existing Module Lifecycle Gates

Current module lifecycle evidence flows through:

```text
manifest
-> intake
-> slot
-> binding
-> validation
-> conformance
-> readiness
-> activation request
-> activation gate
-> blockers
-> registration preview
-> mock runtime
-> operator review
-> release/freeze checks
```

Every gate remains local, metadata-first, and non-executing. The expected gate
result for activation is still blocked.

## Current Safe State

The safe state after AION-105 is:

- module activation remains disabled
- capability activation remains disabled
- runtime registration remains disabled
- extension code loading remains disabled
- package installation remains disabled
- controlled execution remains disabled
- runtime registration preview remains preview-only
- module mock runtime remains synthetic
- Generic Knowledge Intelligence remains metadata-only
- Operator Console module lifecycle views remain read-only

## What Remains Disabled

The following surfaces remain unavailable:

- plugin loader
- executable payload acceptance
- dependency download
- dynamic module import
- dynamic API route registration
- dynamic SDK or CLI registration
- policy action registration from manifests
- active capability invocation
- controlled action handoff
- module runtime execution
- module write path
- privileged bypass

## What Remains Mock-Only

The module mock runtime remains a deterministic evidence layer. It may produce
synthetic dry-run records, redacted output examples, readiness trail evidence,
and operator review inputs. It must not load module code, invoke capabilities,
call external services, fetch dependencies, mutate runtime configuration,
register routes, or activate capabilities.

## Known Gaps

Future activation work still requires:

- activation threat model
- sandbox design
- package trust model
- signed package design
- dependency policy
- runtime registration design
- operator approval model
- audit and provenance design for execution boundaries
- rollback and disable design
- production auth dependency review
- release gate dependency review
- minimum test matrix for activation implementation

## Review Decision

AION-105 approves the current module activation design for continued planning
and evidence review only. Activation is not approved.

The design review decision is:

- current metadata-only module lifecycle gates are coherent
- plugin boundaries are explicit enough for future architecture work
- disabled and mock-only states are release blockers if weakened
- future activation work must pass the pre-gate before implementation begins

## Next Phase Recommendation

The next module activation phase should remain design-first. It should produce
the threat model, sandbox architecture, dependency trust model, signed package
design, rollback design, operator approval model, and release gate before any
runtime implementation. No future task should enable activation unless its ADR
explicitly supersedes this AION-105 gate.
