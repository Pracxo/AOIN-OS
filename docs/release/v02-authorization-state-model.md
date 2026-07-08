# v0.2 Authorization State Model

## Purpose

AION-147 defines the preview state model for implementation authorization and
runtime enablement guard review. No state approves implementation or enables
runtime.

## States

| State | Meaning | Approval effect |
| --- | --- | --- |
| `drafted` | The preview record is started. | None. |
| `approval_record_drafted` | The explicit approval record schema is present. | None. |
| `evidence_attached` | Required evidence references are attached. | None. |
| `guard_bound` | Runtime enablement guard fields are bound. | None. |
| `authorization_review_preview` | Review evidence can be inspected. | None. |
| `authorization_pending` | Future authorization is still pending. | None. |
| `authorization_blocked` | Missing evidence or no-go state blocks authorization. | None. |
| `rejected` | Candidate is rejected. | None. |
| `expired` | Candidate authorization window has expired. | None. |
| `revoked` | Candidate authorization has been revoked. | None. |
| `authorization_unapproved` | Authorization remains unapproved. | None. |
| `implementation_unapproved` | Implementation remains unapproved. | None. |

## Non-Approval Statement

No state in this model approves implementation or enables runtime. The current
state remains `authorization_unapproved` and `implementation_unapproved` with
`implementation_authorization_approved=false`,
`explicit_approval_record_approval=false`, and
`runtime_enablement_guard_release_approved=false`.

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
