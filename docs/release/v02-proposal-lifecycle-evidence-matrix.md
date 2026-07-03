# v0.2 Proposal Lifecycle Evidence Matrix

| Proposal state | Required evidence | Required reviewer | Allowed today | Implementation approved | Runtime enabled | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| drafted | problem statement | workstream owner | true | false | false | implementation approval set true | Draft only. |
| submitted | problem and risk statements | release governance | true | false | false | approval queue item approved true | Intake only. |
| intake_review | required fields complete | policy reviewer | true | false | false | approval workflow bypassed | Review only. |
| evidence_required | missing evidence list | security reviewer | true | false | false | approval record missing | Blocks approval. |
| adr_required | ADR dependency | architecture reviewer | true | false | false | ADR dependency bypassed | Blocks approval. |
| gate_required | gate dependency | release reviewer | true | false | false | gate dependency bypassed | Blocks approval. |
| security_review_required | security impact | security reviewer | true | false | false | external calls enabled | Blocks runtime. |
| architecture_review_required | architecture impact | architecture reviewer | true | false | false | runtime API execution routes added | Blocks runtime. |
| operator_review_required | operator impact | operator reviewer | true | false | false | operator write execution enabled | Blocks writes. |
| queued_for_future_decision | full evidence pack | dual-control reviewers | true | false | false | workstream implementation approval set true | Queue only. |
| rejected | rejection reason | release governance | true | false | false | proposal implementation approval true | Closed. |
| expired | expiry reason | release governance | true | false | false | approval expiry bypassed | Closed. |
| revoked | revocation reason | release governance | true | false | false | approval revocation bypassed | Closed. |
| implementation_unapproved | no-go acknowledgement | release governance | true | false | false | runtime implementation approved true | Terminal lock. |

All implementation approved and runtime enabled values remain false.
