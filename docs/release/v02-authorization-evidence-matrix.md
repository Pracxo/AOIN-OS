# v0.2 Authorization Evidence Matrix

| Authorization area | Required evidence | Required reviewer | Required ADR | Required gate | Approval record state | Authorization state | Runtime guard release state | Runtime enabled | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Implementation authorization preview | Preview record, no-go acknowledgement, explicit schema | Architecture reviewer | ADR 0138 | `v02-implementation-authorization-preview-check.sh` | `explicit_approval_record_approval=false` | `implementation_authorization_approved=false` | `runtime_enablement_guard_release_approved=false` | false | Yes | Preview-only. |
| Runtime enablement guard | Guard boundary and lock evidence | Security reviewer | ADR 0138 | `v02-runtime-enablement-guard-freeze.sh` | `approval_status=false` | `authorization_unapproved` | false | false | Yes | Guard release remains blocked. |
| Approval vote record dependency | Vote record closeout evidence | Review board reviewer | ADR 0137 | `v02-runtime-approval-board-final-review.sh` | false | false | false | false | Yes | Vote records do not approve implementation. |
| Go/no-go ledger dependency | Final no-go ledger lock | Operator reviewer | ADR 0137 | `v02-implementation-go-no-go-final-freeze.sh` | false | false | false | false | Yes | `implementation_go_status=false`. |
| Release boundary | No tag and no release evidence | Release reviewer | ADR 0138 | `scripts/check.sh` | false | false | false | false | Yes | No v0.2 tag or release. |

## AION-148 Implementation Authorization Stabilization

AION-148 freezes the implementation authorization preview, explicit approval
record schema, and runtime enablement guard boundary into a stable evidence
baseline. It remains non-approving: `implementation_authorization_preview_only=true`,
`implementation_authorization_approved=false`,
`implementation_authorization_stabilization_approval=false`,
`explicit_approval_record_approval=false`,
`explicit_approval_record_freeze_approval=false`,
`runtime_enablement_guard_release_approved=false`,
`runtime_approval_board_decision_approved=false`, `implementation_go_status=false`,
and `runtime_implementation_approved=false`. No v0.2 tag or release is created.

## AION-149 Implementation Authorization Final Review

AION-149 adds final review, explicit approval record closeout, and runtime
enablement guard final lock evidence while keeping final review approval,
approval record closeout approval, and runtime guard final lock release approval
false.
