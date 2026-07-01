# v0.2 Decision Review Calendar

## Decision Review Cadence

v0.2 planning reviews occur before a backlog item can move toward
implementation. Reviews are planning-only and do not approve runtime behavior.

## Required Attendees And Roles

Required roles are:

- product owner placeholder
- operator reviewer placeholder
- security reviewer placeholder
- architecture reviewer placeholder
- audit/provenance reviewer placeholder
- rollback reviewer placeholder

## Decision Inputs

Decision inputs must include the backlog intake record, candidate workstream,
required ADR, required gate, no-go statement, security review requirement,
rollback/audit requirement, operator review requirement, and current approval
state.

## Review Outputs

Review outputs are one of:

- remains blocked
- needs ADR
- needs gate evidence
- needs security review
- needs rollback/audit evidence
- ready for future implementation proposal

Review output never changes implementation approval by itself.

## Approval Restrictions

Planning review cannot approve runtime implementation, backlog implementation,
operator write execution, connector runtime, production auth, module
activation, external calls, credential storage, token storage, sandbox
execution, v0.2 tag creation, or v0.2 release creation.

## ADR Creation Requirements

If review output is ready for a future proposal, the next step is a scoped ADR.
The ADR must name behavior, approval state changes, security review, rollback,
audit/provenance, operator review, and no-go regression evidence.

## Gate Evidence Requirements

Gate evidence must include prior planning gates, scoped implementation gate,
scoped no-go regression, rollback readiness gate, audit/provenance gate,
security review evidence, operator review evidence, and full repository check
evidence.

## No-Go Triggers

No-go triggers are implementation approval set true, backlog item marked
implementation-approved, v0.2 release or tag creation, production auth enabled,
connector runtime enabled, operator write execution enabled, module activation
enabled, external calls enabled, credential/token storage enabled, sandbox
execution enabled, package or migration drift, runtime API execution routes,
or privileged bypass.
