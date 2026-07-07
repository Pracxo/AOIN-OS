# v0.2 Approval Vote Record Guard

AION-144 creates a preview-only approval vote record guard. The guard records
that a future approval vote record shape exists, but it does not approve
implementation, release runtime, or change runtime state.

## Required State

- `approval_vote_record_created=true`
- `approval_vote_record_approval=false`
- `approval_vote_record_runtime_effect=false`
- `runtime_approval_board_decision_approved=false`
- `runtime_approval_lock_release_approved=false`
- `runtime_approval_review_approved=false`
- `implementation_decision_record_approval=false`
- `approval_docket_item_approved=false`
- `runtime_decision_readiness_approved=false`
- `runtime_implementation_approved=false`
- `decision_package_approval=false`
- `approval_readiness_approved=false`
- `review_board_decision_approval=false`
- `routing_decision_approval=false`
- `reviewer_signoff_implementation_approval=false`
- `v02_release_approved=false`

## Guard Rules

Approval vote records are evidence attachments only. They cannot be interpreted
as implementation approval, runtime approval, release approval, reviewer
sign-off approval, routing approval, approval readiness approval, or runtime
decision readiness approval.

Any vote record with approval or runtime effect set true is a no-go condition.
Any missing vote record is also a blocker for future approval-board review, but
missing evidence does not authorize bypass.

## Runtime Boundary

The vote record guard does not enable connector runtime, operator write
execution, production auth, module activation, external calls, credential
storage, token storage, or sandbox execution.
