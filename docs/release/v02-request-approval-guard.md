# v0.2 Request Approval Guard

## Guard Purpose

The request approval guard records the exact approval defaults required before
any future v0.2 implementation request can be considered. It prevents evidence
or gate success from being treated as approval.

## Required False Approval States

- `request_pack_approval=false`
- `submission_approval=false`
- `runtime_implementation_approved=false`
- `backlog_implementation_items_approved=false`
- `workstream_implementation_approved=false`
- `proposal_implementation_approved=false`
- `approval_queue_item_approved=false`
- `operator_write_execution_approved=false`
- `connector_implementation_approved=false`
- `production_auth_approved=false`
- `module_activation_approved=false`
- `external_calls_approved=false`
- `credential_storage_approved=false`
- `token_storage_approved=false`
- `sandbox_execution_approved=false`
- `v02_release_approved=false`

## Guard Decision

AION-133 does not create approval records, approve request packs, approve
submissions, approve runtime implementation, approve backlog implementation
items, approve workstream implementation, approve proposal implementation,
approve approval queue items, approve release creation, approve tag creation,
or approve privileged bypass.

## AION-134 Registry Guard Extension

AION-134 extends this guard to submission registry and pre-approval queue
records. Registry preview and queue preview records cannot approve submissions,
preapproval queue items, request packs, implementations, releases, tags, or
privileged bypass.

## AION-135 Submission Registry Stabilization Dependency

AION-135 keeps this request approval guard active for all stabilized request
candidates. Request approval, submission approval, preapproval queue item
approval, implementation approval, runtime approval, approval workflow bypass,
approval record missing, ADR dependency bypass, and gate dependency bypass all
remain blocked conditions.

AION-136 adds review-board routing to the guard. Review board decision
approval, reviewer sign-off as approval, routing readiness as approval,
preapproval queue approval, request pack approval, submission approval, and
implementation approval remain blocked conditions.

AION-137 adds review routing freeze and quorum evidence to the guard. Review
board decision approval, routing decision approval, reviewer sign-off as
implementation approval, preapproval queue approval, request pack approval,
submission approval, and implementation approval remain blocked conditions.

AION-138 adds decision package preview and approval-readiness evidence to the
guard. Decision package approval, approval readiness approval, review board
decision approval, routing decision approval, reviewer sign-off as
implementation approval, preapproval queue approval, request pack approval,
submission approval, and implementation approval remain blocked conditions.

AION-139 adds runtime decision readiness approval to the same blocked
conditions. Stabilization, approval readiness freeze, runtime decision
closeout, ADR dependency presence, and gate dependency success cannot bypass
request approval guard requirements.
