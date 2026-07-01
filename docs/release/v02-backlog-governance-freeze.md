# v0.2 Backlog Governance Freeze

## Planning-Only Backlog Rules

v0.2 backlog items may describe implementation candidates, risks, ADR needs,
gate dependencies, review owners, rollback expectations, and audit evidence.
They must not approve or implement runtime behavior.

## Accepted Intake Fields

Accepted backlog intake fields are:

- problem statement
- risk statement
- candidate workstream
- ADR dependency
- gate dependency
- security review requirement
- rollback and audit requirement
- owner placeholder
- no-go statement
- evidence references
- implementation approval state

## Rejected Intake Conditions

Reject any backlog item that marks implementation approved, requests a v0.2
tag or release, enables production auth, enables connector runtime, enables
operator write execution, enables module activation, enables external calls,
stores credentials or tokens, enables sandbox execution, adds package files,
adds migrations, adds runtime API routes, or bypasses approval, policy, audit,
or operator review.

## Required ADR Mapping

Each backlog item must map to a future scoped ADR before implementation can be
considered. The ADR must name the allowed behavior, blocked behavior, approval
state change, rollback model, audit/provenance model, security review, and
operator review evidence.

## Required Gate Mapping

Each backlog item must map to existing planning gates and future scoped gates:

- v0.2 planning stabilization gate
- planning stabilization no-go regression
- scoped implementation gate
- scoped no-go regression
- rollback readiness gate
- audit/provenance gate
- operator review gate

## Security Review Requirement

Security review is required before any implementation proposal can move beyond
planning. The review must cover authorization, protected material, external
egress, rollback, audit evidence, and no-go regression coverage.

## Rollback And Audit Requirement

Every backlog item must describe rollback and audit requirements before
implementation. Rollback must avoid hard delete and audit must remain
tamper-evident and redacted.

## Implementation Approval Remains False

AION-120 keeps `runtime_implementation_approved=false` and keeps every scoped
implementation approval false. Backlog intake does not grant implementation
approval.

## No-Go Conditions

No-go conditions are v0.2 tag creation, v0.2 release creation, any
implementation approval set true, production auth enabled, connector runtime
enabled, operator write execution enabled, module activation enabled, external
calls enabled, credential/token storage enabled, sandbox execution enabled,
package files added, migrations added, runtime API execution routes added, or
backlog items marked implementation-approved.

## AION-121 Closeout Dependency

AION-121 keeps this backlog freeze active during planning closeout. Backlog
items remain planning-only and cannot be treated as implementation-approved
without a future scoped ADR, scoped gate, security review, rollback evidence,
audit/provenance evidence, operator review, and no-go regression.
