# v0.2 Runtime Approval Board Lifecycle Evidence Matrix

AION-145 stabilizes the runtime approval board lifecycle as evidence only. The
matrix keeps each board state tied to required records and blockers without
granting implementation approval.

| Board state | Required evidence | Required reviewer | Required ADR | Required gate | Runtime approval board decision state | Approval vote record state | Go/no-go ledger state | Runtime enabled | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drafted | candidate summary, blocker summary | planning reviewer | future candidate ADR | candidate intake gate | false | not attached | no-go true | false | missing candidate summary | Drafted state is evidence only. |
| docketed | approval docket item and lock evidence | docket reviewer | approval docket ADR | approval docket final review | false | not attached | no-go true | false | approval docket item approved true | Docketing is not approval. |
| vote_record_attached | synthetic vote record freeze | vote reviewer | vote record ADR | approval vote record stabilization freeze | false | approval false, runtime effect false | no-go true | false | vote record approval true | Vote records cannot approve implementation. |
| ledger_entry_attached | go/no-go ledger evidence | release reviewer | go/no-go ledger ADR | stabilization no-go regression | false | approval false | go false, no-go true | false | implementation go true | Ledger entries remain blocking. |
| evidence_attached | docs, examples, static console, gate output | evidence reviewer | evidence ADR | docs and final docs audit | false | approval false | no-go true | false | evidence completeness bypassed | Evidence completeness cannot bypass approval. |
| quorum_preview | reviewer role matrix and quorum preview | review-board reviewer | review board ADR | review board stabilization gate | false | approval false | no-go true | false | reviewer sign-off marked implementation approval true | Quorum is preview-only. |
| approval_board_review_preview | board review summary | runtime approval reviewer | runtime board ADR | runtime approval board stabilization gate | false | approval false | no-go true | false | runtime approval board stabilization approval true | Review is not a decision approval. |
| go_no_go_preview | no-go ledger summary | release gate reviewer | release gate ADR | final planning release gate | false | approval false | go false, no-go true | false | go/no-go ledger runtime effect true | No candidate is marked go. |
| blocked | blocker register | accountable reviewer | blocker ADR when created | blocker-specific gate | false | approval false | no-go true | false | blocker bypassed | Blocked state is the default for candidates. |
| rejected | rejection reason | decision reviewer | future rejection ADR | rejection gate | false | approval false | no-go true | false | rejection used as runtime approval | Rejection cannot approve implementation. |
| expired | expiry evidence | approval workflow reviewer | workflow ADR | approval workflow gate | false | approval false | no-go true | false | expiry bypassed | Expired evidence must be refreshed later. |
| revoked | revocation evidence | approval workflow reviewer | workflow ADR | approval workflow gate | false | approval false | no-go true | false | revocation bypassed | Revoked evidence stays non-authorizing. |
| approval_board_unapproved | stabilization summary | board reviewer | ADR 0136 | stabilization gate | false | approval false | no-go true | false | board decision approval true | AION-145 closes here. |
| implementation_unapproved | implementation lock summary | release reviewer | final planning ADR | final planning release gate | false | approval false | no-go true | false | runtime implementation approval true | No implementation can proceed. |

## Lifecycle Boundary

- `runtime_approval_board_preview_only=true`
- `runtime_approval_board_decision_approved=false`
- `runtime_approval_board_stabilization_approval=false`
- `approval_vote_record_approval=false`
- `approval_vote_record_runtime_effect=false`
- `implementation_go_status=false`
- `go_no_go_ledger_runtime_effect=false`
- `runtime_implementation_approved=false`
