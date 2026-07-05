# v0.2 Pre-Approval Review Board

## Purpose

AION-136 defines the v0.2 pre-approval review board as a planning-only routing body for future implementation candidates. The board gives submissions a deterministic reviewer path before any future approval can be considered.

## Scope

The review board covers submission intake, reviewer role assignment, evidence readiness, ADR dependency checks, gate dependency checks, and no-go acknowledgement. It does not change runtime behavior, does not add API routes, and does not add SDK or CLI implementation.

## Planning-Only Boundary

Review board is planning-only. Review board does not approve implementation. Review board does not enable runtime. Review board decision approval remains false.

## Required Reviewer Roles

- Requester: supplies the candidate and evidence pack.
- Intake reviewer: confirms the submission is complete enough to route.
- Security reviewer: checks external call, credential, token, auth, sandbox, and privileged bypass risks.
- Architecture reviewer: confirms ADR dependency and boundary fit.
- Operator reviewer: checks operator safety, write-path, rollback, and console readiness.
- Policy reviewer: checks approval policy, no-go, expiry, revocation, and dual-control posture.
- Audit/provenance reviewer: checks evidence traceability and auditability.
- Rollback reviewer: checks recovery evidence and rollback readiness.
- Approver placeholder: reserved for a future approval workflow and cannot approve implementation in AION-136.
- Auditor: verifies records remain review-only and approval false.

## Required Evidence Before Routing

- Submission registry stabilization evidence.
- Request pack final review evidence.
- Request pack stabilization evidence.
- Implementation request pack evidence.
- Planning track closeout evidence.
- Final planning release gate evidence.
- Planning master checkpoint evidence.
- Proposal registry stabilization evidence.
- Docs, final docs audit, no-domain-drift, and boundary check evidence.

## Required ADR Dependency

Every candidate must name an ADR dependency before routing. ADR readiness is not implementation approval.

## Required Gate Dependency

Every candidate must name a gate dependency before routing. Gate readiness is not implementation approval.

## Required No-Go Acknowledgement

Every routed submission must acknowledge the review-board no-go list before future approval can be considered. Acknowledgement does not approve implementation.

## Review Decision States

| State | Meaning | Implementation approval | Runtime enabled |
| --- | --- | --- | --- |
| intake_pending | Submission exists but routing is not complete. | false | false |
| evidence_incomplete | Required evidence is missing. | false | false |
| routed_for_review | Reviewer roles are assigned for planning review. | false | false |
| blocked_by_no_go | A no-go condition blocks review progression. | false | false |
| ready_for_future_decision | Evidence is ready for a future decision process. | false | false |

## No Tag Or Release

AION-136 creates no v0.2 tag and no v0.2 release. AION Brain v0.1.0 remains frozen and untouched.

## AION-137 Stabilization Handoff

AION-137 stabilizes this review board into a routing freeze and
decision-readiness evidence baseline. The handoff remains planning-only:
review board decision approval, routing decision approval, reviewer sign-off
implementation approval, submission approval, preapproval queue approval,
request pack approval, and runtime implementation approval remain false.

## AION-138 Decision Package Handoff

AION-138 consumes this review board as decision package evidence only.
Decision package approval, approval readiness approval, review board decision
approval, routing decision approval, reviewer sign-off implementation
approval, submission approval, preapproval queue approval, request pack
approval, and runtime implementation approval remain false.
