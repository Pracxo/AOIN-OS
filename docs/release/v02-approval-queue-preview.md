# v0.2 Approval Queue Preview

## Queue Purpose

AION-126 adds a preview queue for future workstream proposal review. The queue shows which proposals have enough planning evidence to be considered later, but it remains a read-only preview over synthetic records.

## Queue State Is Preview-Only

The queue state is preview-only. Queue placement is not approval, execution, release authorization, tag authorization, runtime enablement, or merge authorization.

## Queue Does Not Approve Implementation

The queue does not approve implementation. `approval_queue_item_approved=false`, `workstream_implementation_approved=false`, and `runtime_implementation_approved=false` remain required for every queue item.

## Queue Does Not Enable Runtime

The queue does not enable runtime. Production auth, connector runtime, operator write execution, module activation, external calls, credential storage, token storage, sandbox execution, code loading, runtime registration, and capability activation remain disabled or absent.

## Required Reviewers

Future queue advancement requires security review, architecture review, operator review, policy review, and rollback/audit review. Missing reviewer evidence returns the proposal to evidence required or rejection.

## Required Evidence

Every queue item must cite the problem statement, risk statement, security impact, architecture impact, policy impact, audit/provenance impact, rollback plan, ADR dependency, gate dependency, test evidence, and no-go acknowledgement.

## Expiry And Revocation Rules

Queue entries expire if evidence becomes stale, the ADR dependency changes, the gate dependency changes, or a blocker becomes unresolved. Queue entries are revoked if no-go evidence fails, approval workflow bypass is detected, approval records are missing, or runtime enablement is requested directly.

## Dual-Control Requirement

Future approval requires dual-control. A single reviewer, script, queue flag, or preview record cannot approve implementation.

## Approval Status Remains False

Approval status remains false for every queue item. The queue may show `queued_for_future_decision`, but it must also show implementation unapproved.

## No-Go Conditions

The queue fails if a queue item is marked approved, implementation approval is set true, workstream implementation approval is set true, approval workflow bypass is true, an approval record is missing, ADR dependency is bypassed, gate dependency is bypassed, production auth is enabled, connector runtime is enabled, operator write execution is enabled, module activation is enabled, external calls are enabled, credential or token storage is enabled, sandbox execution is enabled, package files are added, migrations are added, runtime API execution routes are added, a v0.2 tag is created, or a v0.2 release is created.

## AION-127 Approval Queue Freeze

AION-127 freezes this queue as preview-only evidence. Queue item approval,
proposal implementation approval, implementation approval, workstream
implementation approval, backlog implementation approval, approval workflow
bypass, approval record missing, ADR dependency bypass, gate dependency
bypass, approval expiry bypass, approval revocation bypass, dual-control
bypass, v0.2 tag creation, and v0.2 release creation remain false.
