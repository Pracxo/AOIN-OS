# v0.2 Approval Decision Record

## Decision ID

`TBD`

## Requested Workstream

`TBD`

## Decision Status

Default decision status: not approved.

## Approval Status

Default approval status: false.

- `runtime_implementation_approved=false`
- `backlog_implementation_items_approved=false`

## Required ADR

The scoped ADR must be named before approval can be considered.

## Required Gate

The scoped gate and no-go regression must be named before approval can be
considered.

## Evidence Links

Evidence links are repository-local document and script references only.

## Reviewers

Required reviewers:

- requester
- reviewer
- approver
- security reviewer
- architecture reviewer
- operator reviewer

## Expiry

Every approval decision must expire. Default: not approved until an expiry is
defined.

## Revocation Path

Revocation may be triggered by failed gate evidence, failed security review,
failed architecture review, failed operator review, scope drift, or a no-go
condition.

## Notes

Approval does not execute work and does not enable runtime by itself.

## Default Decision

Default decision: not approved.

## AION-123 Decision Evidence

AION-123 requires every future decision record to map workstream, required ADR,
required gate, required evidence, required reviewers, approval status, runtime
approval status, release blocker status, expiry, revocation path, and
dual-control status where required. Missing evidence keeps the decision not
approved.
