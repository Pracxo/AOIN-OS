# v0.2 Reviewer Quorum Model

The review board quorum model defines future review roles without granting implementation approval or runtime enablement.

| Role | Responsibility | Evidence required | Decision boundary |
| --- | --- | --- | --- |
| Requester | Frames the candidate and supplies the initial evidence packet. | Submission record, request pack reference, blocker statement. | Cannot approve implementation alone and cannot enable runtime. |
| Intake reviewer | Confirms the submission is complete enough to route. | Intake checklist, required documents, missing-evidence list. | Cannot approve implementation alone and cannot enable runtime. |
| Security reviewer | Reviews auth, credential, token, external call, and sandbox risks. | Threat notes, no-go acknowledgement, required security gate. | Cannot approve implementation alone and cannot enable runtime. |
| Architecture reviewer | Checks ADR dependency, system boundary, and runtime architecture impact. | ADR dependency, gate dependency, architecture notes. | Cannot approve implementation alone and cannot enable runtime. |
| Operator reviewer | Checks operator console, write execution, rollback, and observability posture. | Operator evidence, rollback evidence, disabled write controls. | Cannot approve implementation alone and cannot enable runtime. |
| Policy reviewer | Confirms policy, approval, and governance locks remain intact. | Policy lock evidence, approval state ledger, no bypass record. | Cannot approve implementation alone and cannot enable runtime. |
| Audit/provenance reviewer | Checks provenance, audit trail, evidence redaction, and source grounding. | Audit evidence, provenance references, redaction confirmation. | Cannot approve implementation alone and cannot enable runtime. |
| Rollback reviewer | Confirms rollback and recovery readiness before future approval. | Rollback plan, recovery blocker, dry-run readiness statement. | Cannot approve implementation alone and cannot enable runtime. |
| Approver placeholder | Reserved for a future explicit approval workflow. | Future approval record only. | Cannot approve implementation in AION-137 and cannot enable runtime. |
| Auditor | Observes review-board evidence and checks no-go outcomes. | Audit notes, no-go regression result, final checklist. | Cannot approve implementation alone and cannot enable runtime. |

## Quorum Expectation

A future review quorum requires intake, security, architecture, operator, policy, audit/provenance, and rollback evidence before a candidate can be marked decision-ready.

Quorum expectation is not implementation approval. It only records which evidence must be present before a future decision workflow can be considered.

## Conflict-of-Interest Rule

The requester cannot be the sole reviewer for their own candidate. A reviewer with direct implementation ownership must disclose that relationship and cannot satisfy quorum alone.

## Dual-Control Option

High-risk candidates may require dual-control review from security plus architecture, policy plus audit/provenance, or operator plus rollback. Dual-control review is evidence only until a future explicit approval record exists.

No reviewer can approve implementation alone.

No reviewer can enable runtime.
