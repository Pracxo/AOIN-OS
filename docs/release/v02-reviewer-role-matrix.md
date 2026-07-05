# v0.2 Reviewer Role Matrix

| Role | Responsibility | Decision boundary | Cannot approve implementation alone | Cannot enable runtime | Evidence required | Conflict-of-interest notes |
| --- | --- | --- | --- | --- | --- | --- |
| requester | Prepares the candidate and evidence pack. | May request routing only. | yes | yes | candidate scope, evidence links, ADR and gate dependencies | Cannot review or approve their own submission. |
| intake reviewer | Checks completeness and routes to reviewers. | May mark evidence complete enough for routing. | yes | yes | checklist, submission record, missing-evidence notes | Must not be the requester. |
| security reviewer | Reviews auth, credential, token, external call, sandbox, and bypass risk. | May block unsafe candidates. | yes | yes | no-go scan, threat notes, credential/token absence proof | Must disclose ownership of security implementation work. |
| architecture reviewer | Reviews ADR dependency and boundary fit. | May require ADR changes before future decision. | yes | yes | ADR link, architecture boundary evidence, dependency matrix | Must disclose authorship of the candidate architecture. |
| operator reviewer | Reviews operator safety and console/readiness impact. | May block write-path or activation candidates. | yes | yes | operator runbook, rollback notes, static-console safety evidence | Must not be the requester for operator execution candidates. |
| policy reviewer | Reviews approval policy, expiry, revocation, and dual-control posture. | May require policy evidence before decision readiness. | yes | yes | policy matrix, approval workflow evidence, no-go acknowledgement | Must not bypass approval records. |
| audit/provenance reviewer | Reviews traceability and audit evidence. | May require provenance evidence before routing completion. | yes | yes | audit ledger references, evidence matrix, docs audit result | Must disclose ownership of audit implementation. |
| rollback reviewer | Reviews rollback, recovery, and hard-delete absence. | May require recovery evidence before future decision. | yes | yes | rollback plan, recovery scenarios, hard-delete absence proof | Must not review recovery work they authored alone. |
| approver placeholder | Reserved for a future approval workflow. | No approval authority in AION-136. | yes | yes | future approval record placeholder only | Cannot issue approval in this milestone. |
| auditor | Confirms review records remain planning-only and approval false. | May flag drift or missing records. | yes | yes | final evidence pack, no-go result, tag/release absence proof | Must remain independent from requester and approver placeholder. |

No role can approve implementation alone. No role can enable runtime.

## AION-137 Quorum Handoff

AION-137 stabilizes the reviewer role matrix into a quorum model. Quorum is
evidence only: no reviewer, reviewer group, reviewer sign-off, approver
placeholder, or auditor note can approve implementation or enable runtime.
