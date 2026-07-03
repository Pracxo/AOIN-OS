# v0.2 Approval Queue Freeze

## Queue Remains Preview-Only

The approval queue is a static planning preview. It can show candidate proposals and missing evidence, but it does not create approval records.

## Queue Does Not Approve Implementation

Queue placement is not approval. `proposal_implementation_approved=false`, `workstream_implementation_approved=false`, and `backlog_implementation_items_approved=false` remain locked.

## Queue Does Not Enable Runtime

The queue cannot enable runtime implementation, production auth, connector runtime, operator write execution, module activation, external calls, credential storage, token storage, or sandbox execution.

## Queue Item Approval Remains False

Every queue item keeps `approval_queue_item_approved=false` until a later scoped implementation task explicitly widens scope with approval records, ADRs, and gate evidence.

## Required Reviewers

Required reviewers are architecture, security, policy, operator, audit/provenance, and release governance owners. Their presence in the queue is descriptive only.

## Required Evidence

Required evidence includes problem statement, risk statement, security impact, architecture impact, policy impact, audit/provenance impact, rollback plan, ADR dependency, gate dependency, test evidence, no-go acknowledgement, expiry, revocation, and dual-control evidence.

## Expiry And Revocation Rules

Missing or stale evidence moves an item to expired or revoked and keeps all approval states false. Expiry and revocation cannot be bypassed.

## ADR Dependency Rule

Every candidate must name a future ADR before implementation can be considered. A missing ADR dependency blocks the item.

## Gate Dependency Rule

Every candidate must name a future release or safety gate before implementation can be considered. A missing gate dependency blocks the item.

## No-Go Conditions

The freeze fails on approval queue item approved true, proposal implementation approval true, implementation approval true, workstream implementation approval true, backlog implementation approval true, approval workflow bypass, missing approval record, ADR dependency bypass, gate dependency bypass, approval expiry bypass, approval revocation bypass, dual-control bypass, v0.2 tag or release creation, production auth enablement, connector runtime enablement, operator write execution enablement, module activation enablement, external calls, credential/token storage, sandbox execution, package files, migrations, or runtime API execution routes.

## AION-128 Planning Master Checkpoint

AION-128 consumes this approval queue freeze as an inherited planning baseline.
The queue remains preview-only, queue placement remains non-approval, approval
queue item approval remains false, proposal implementation approval remains
false, and no runtime or release behavior is enabled.
