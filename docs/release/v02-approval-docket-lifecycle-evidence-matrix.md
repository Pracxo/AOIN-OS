# v0.2 Approval Docket Lifecycle Evidence Matrix

The lifecycle evidence matrix maps every approval docket state to required evidence and blocked runtime outcomes. It is a stabilization artifact only and does not approve implementation.

| Lifecycle state | Required evidence | Approval state | Runtime state | Blocker |
| --- | --- | --- | --- | --- |
| drafted | decision package reference | false | disabled | missing reviewer evidence |
| docketed | approval docket entry | false | disabled | missing decision record |
| evidence_attached | evidence pack | false | disabled | missing ADR dependency |
| decision_record_attached | implementation decision record | false | disabled | missing gate dependency |
| review_ready_preview | reviewer evidence | false | disabled | runtime review not approved |
| runtime_review_pending | runtime approval review baseline | false | disabled | approval record absent |
| stabilization_frozen | stabilization gate evidence | false | disabled | future approval task required |
| record_freeze_created | implementation decision record freeze | false | disabled | future approval task required |
| blocked | unresolved blocker | false | disabled | blocker open |
| rejected | rejection evidence | false | disabled | approval denied |
| expired | expiry evidence | false | disabled | approval stale |
| revoked | revocation evidence | false | disabled | approval revoked |
| docket_unapproved | no approval record | false | disabled | approval record absent |
| implementation_unapproved | implementation approval false | false | disabled | runtime implementation unapproved |

No lifecycle state approves implementation or enables runtime.

## Matrix Requirements
- Every row must have approval state false.
- Every row must have runtime state disabled.
- Every row must preserve an explicit blocker.
- Every row must reference synthetic, redacted, local evidence.
- No row may create a tag, create a release, enable external calls, store credentials/tokens, enable sandbox execution, add packages, add migrations, or add runtime API execution routes.

## AION-143 Final Lifecycle Handoff
AION-143 adds final review and runtime approval lock evidence without changing lifecycle approval states. Every lifecycle row remains approval state false and runtime state disabled; approval docket final review approval, implementation decision record closeout approval, runtime approval lock release approval, and runtime implementation approval remain false.
