# v0.2 Implementation Request Phase Boundary

## Boundary

After AION-130, implementation requests may be proposed only through the proposal registry. The registry is the intake surface for future work descriptions, evidence references, ADR dependencies, gate dependencies, review requirements, and no-go conditions.

## Registry And Queue State

The proposal registry remains preview-only. The approval queue remains preview-only. Queue placement is ordering evidence only and cannot approve implementation.

## Approval State

`approval_queue_item_approved=false`

`proposal_implementation_approved=false`

`runtime_implementation_approved=false`

`backlog_implementation_items_approved=false`

`workstream_implementation_approved=false`

## Runtime Capability State

No runtime capability is enabled. Connector runtime, operator write execution, production auth, module activation, capability activation, code loading, runtime registration, external calls, credential storage, token storage, sandbox execution, tool execution, action execution, and hard deletes remain blocked.

## Future Implementation Requirements

Future implementation requires explicit approval records, ADRs, and gate evidence before any runtime work can begin. Required evidence includes security review, architecture review, operator review, rollback/audit evidence, no-go regression evidence, and release gate evidence.

## Phase Decision

AION-130 opens the future request phase only as a governed proposal path. It does not open implementation scope.

## AION-131 Request Pack Boundary

AION-131 defines the request package used inside this phase. It keeps the
proposal registry preview-only, keeps the approval queue preview-only, and
keeps request package implementation approval, proposal template
implementation approval, approval evidence approval, approval queue item
approval, proposal implementation approval, workstream implementation
approval, backlog implementation approval, and runtime implementation
approval false.
