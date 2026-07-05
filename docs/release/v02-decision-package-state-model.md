# v0.2 Decision Package State Model

## States

| State | Meaning | Approval status |
| --- | --- | --- |
| evidence_collected | Required planning artifacts are present. | false |
| routed_for_review | Review routing exists as planning evidence. | false |
| package_preview_created | Decision package preview artifacts exist. | false |
| readiness_evidence_bundled | Approval-readiness evidence is bundled. | false |
| blocked_for_approval | Future approval workflow is still required. | false |
| future_decision_required | Explicit future decision record is required. | false |

## Allowed Transitions

- evidence_collected -> routed_for_review
- routed_for_review -> package_preview_created
- package_preview_created -> readiness_evidence_bundled
- readiness_evidence_bundled -> blocked_for_approval
- blocked_for_approval -> future_decision_required

## Disallowed Transitions

- package_preview_created -> runtime implementation approved
- readiness_evidence_bundled -> decision package approved
- blocked_for_approval -> runtime enabled
- future_decision_required -> release created
- future_decision_required -> tag created

The state model is deliberately non-executing. It records readiness posture and
keeps every approval false.

## AION-139 Stabilized State Boundary

AION-139 adds stabilization and approval readiness freeze evidence around this
state model. No state in the stabilized model approves runtime decision
readiness, approves implementation, enables runtime, creates a tag, or creates
a release.
