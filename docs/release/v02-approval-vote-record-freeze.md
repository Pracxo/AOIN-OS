# v0.2 Approval Vote Record Freeze

AION-145 freezes approval vote records as preview-only evidence. Approval vote
records do not approve implementation, do not enable runtime, do not release
the runtime approval lock, and do not change the implementation go/no-go ledger.

Approval vote records do not approve implementation.

## Frozen Vote Record State

- `approval_vote_record_created=true`
- `approval_vote_record_approval=false`
- `approval_vote_record_runtime_effect=false`
- `runtime_approval_board_decision_approved=false`
- `runtime_approval_board_stabilization_approval=false`
- `go_no_go_ledger_runtime_effect=false`
- `implementation_go_status=false`
- `implementation_no_go_status=true`
- `runtime_approval_lock_release_approved=false`
- `runtime_approval_review_approved=false`
- `implementation_decision_record_approval=false`
- `approval_docket_item_approved=false`
- `runtime_decision_readiness_approved=false`
- `runtime_implementation_approved=false`
- `v02_release_approved=false`

## Evidence Boundary

Vote records can record synthetic reviewer evidence, docket references, and
future candidate blockers. They cannot approve, route, activate, execute, store
credentials, call external services, create a release, or create a tag.

## Stabilization Boundary

AION-145 records the vote freeze alongside:

- `v02_runtime_approval_board_stabilized=true`
- `runtime_approval_board_preview_only=true`
- `go_no_go_ledger_created=true`
- `runtime_approval_board_stabilization_approval=false`
- `v02_tag_created=false`
- `v02_release_created=false`

Any future vote that attempts to set approval or runtime effect true is a
release blocker.
