# v0.2 Submission Lifecycle Evidence Baseline

## Purpose

Map the stabilized submission lifecycle evidence for AION-135. All submission
approved, implementation approved, and runtime enabled values remain false.

| Submission state | Required evidence | Required reviewer | Required ADR | Required gate | Allowed today | Submission approved | Implementation approved | Runtime enabled | Release blocker if violated | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drafted | candidate ID and workstream | release governance | future ADR | future gate | true | false | false | false | true | planning record only |
| submitted | evidence bundle reference | release governance | future ADR | future gate | true | false | false | false | true | intake only |
| intake_validated | required fields complete | policy reviewer | future ADR | future gate | true | false | false | false | true | validation only |
| evidence_review | evidence matrix | evidence reviewer | future ADR | future gate | true | false | false | false | true | no approval implied |
| adr_review_required | ADR dependency | architecture reviewer | future ADR | future gate | true | false | false | false | true | ADR must exist before approval |
| gate_review_required | gate dependency | release governance | future ADR | future gate | true | false | false | false | true | gate must pass before approval |
| security_review_required | threat and safety evidence | security reviewer | future ADR | future gate | true | false | false | false | true | security review only |
| architecture_review_required | architecture impact evidence | architecture reviewer | future ADR | future gate | true | false | false | false | true | no runtime change |
| operator_review_required | operator workflow evidence | operator platform reviewer | future ADR | future gate | true | false | false | false | true | no write path |
| queued_for_preapproval_review | queue placement evidence | release governance | future ADR | future gate | true | false | false | false | true | queue item approval false |
| rejected | rejection reason | release governance | future ADR | future gate | true | false | false | false | true | may be resubmitted later |
| expired | expiry reason | release governance | future ADR | future gate | true | false | false | false | true | stale evidence blocked |
| revoked | revocation reason | release governance | future ADR | future gate | true | false | false | false | true | revoked entries blocked |
| submission_unapproved | explicit approval absence | release governance | future ADR | future gate | true | false | false | false | true | final lock state |
| implementation_unapproved | explicit implementation absence | release governance | future ADR | future gate | true | false | false | false | true | runtime remains disabled |

No lifecycle state approves implementation or enables runtime.
