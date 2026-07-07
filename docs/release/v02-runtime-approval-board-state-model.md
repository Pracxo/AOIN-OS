# v0.2 Runtime Approval Board State Model

AION-144 defines a preview-only state model for future runtime approval board
records. No state approves implementation or enables runtime.

## States

- `drafted`
- `docketed`
- `vote_record_attached`
- `ledger_entry_attached`
- `evidence_attached`
- `quorum_preview`
- `approval_board_review_preview`
- `go_no_go_preview`
- `blocked`
- `rejected`
- `expired`
- `revoked`
- `approval_board_unapproved`
- `implementation_unapproved`

## State Rules

All states remain planning and evidence states. No state can create an approval
record, release a runtime approval lock, mark an implementation candidate go,
enable connector runtime, enable operator write execution, enable production
auth, enable module activation, permit external calls, store credentials, store
tokens, enable sandbox execution, create a v0.2 tag, or create a v0.2 release.

`approval_board_unapproved` and `implementation_unapproved` are terminal safe
states for AION-144. Future implementation still requires explicit approval
records, ADRs, and gate evidence.

## AION-145 Lifecycle Handoff

AION-145 stabilizes the state model into a lifecycle evidence matrix. All board
states remain preview, blocked, rejected, expired, revoked, unapproved, or
implementation-unapproved states unless a later task creates explicit approval
records, ADRs, and gate evidence. Runtime approval board stabilization approval
and runtime implementation approval remain false.
