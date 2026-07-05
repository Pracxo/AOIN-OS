# v0.2 Pre-Approval Queue Freeze

## Purpose

Freeze the pre-approval queue as a preview-only baseline after AION-134. The
queue orders future review work but does not approve implementation.

## Queue Boundary

- Pre-approval queue remains preview-only.
- Queue does not approve implementation.
- Queue does not enable runtime.
- Pre-approval queue item approval remains false.
- Submission approval remains false.
- Request pack approval remains false.

## Required Reviewers

- architecture reviewer
- security reviewer
- policy reviewer
- operator platform reviewer
- audit/provenance reviewer
- release governance reviewer

## Required Evidence

Each queued candidate must include candidate ID, workstream, submission status,
required ADR, required gate, evidence bundle, current blocker, and next
planning action.

## ADR Dependency Requirement

Every queued candidate must point to a future ADR or an existing ADR that
explicitly names the implementation boundary. ADR dependency bypass is a
release blocker.

## Gate Dependency Requirement

Every queued candidate must name the gate that must pass before approval can be
considered. Gate dependency bypass is a release blocker.

## Expiry And Revocation Expectations

Pre-approval queue entries are provisional. Entries must expire when evidence is
stale and must be revocable before any approval workflow can continue.

## No-Go Conditions

The queue fails if a preapproval queue item approved true marker appears, if
submission approval true appears, if request pack approval true appears, if
implementation approval true appears, if approval workflow bypass is present,
if approval record missing is present, if ADR or gate dependencies are
bypassed, if external calls are enabled, if credentials or tokens are stored, if
sandbox execution is enabled, if package files or migrations are added, or if a
v0.2 tag or release is created.

## AION-136 Review Board Handoff

AION-136 routes future submissions through a pre-approval review board without
unfreezing this queue. Queue placement remains preview-only, preapproval queue
item approval remains false, and review board decision approval remains false.

## AION-137 Review Routing Freeze Handoff

AION-137 stabilizes review routing without unfreezing this queue. Queue
placement remains preview-only, preapproval queue item approval remains false,
routing decision approval remains false, reviewer sign-off implementation
approval remains false, and review board decision approval remains false.

## AION-138 Decision Package Handoff

AION-138 packages this queue freeze as approval-readiness evidence only. Queue
placement remains preview-only, preapproval queue item approval remains false,
decision package approval remains false, approval readiness approved remains
false, routing decision approval remains false, reviewer sign-off
implementation approval remains false, and review board decision approval
remains false.
