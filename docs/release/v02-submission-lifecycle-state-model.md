# v0.2 Submission Lifecycle State Model

## States

- drafted
- submitted
- intake_validated
- evidence_review
- adr_review_required
- gate_review_required
- security_review_required
- architecture_review_required
- operator_review_required
- queued_for_preapproval_review
- rejected
- expired
- revoked
- submission_unapproved
- implementation_unapproved

## Runtime Boundary

No lifecycle state approves implementation or enables runtime. State movement is
planning metadata only. A submitted, intake validated, evidence review, ADR
review, gate review, security review, architecture review, operator review, or
queued for preapproval review state still keeps `submission_approval=false` and
`implementation_approval=false`.

## Terminal Planning States

Rejected, expired, revoked, submission unapproved, and implementation
unapproved states are blockers. They do not hard-delete records and do not
grant bypass authority.

## AION-135 Evidence Baseline Handoff

AION-135 maps the lifecycle into
`docs/release/v02-submission-lifecycle-evidence-baseline.md`. The lifecycle
still allows planning states only; submission approved, implementation
approved, and runtime enabled remain false in every state.
