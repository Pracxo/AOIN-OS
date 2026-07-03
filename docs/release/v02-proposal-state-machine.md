# v0.2 Proposal State Machine

## Purpose

The AION-126 proposal state machine describes planning-only movement through the workstream proposal registry. It does not approve implementation or enable runtime.

## States

- drafted: the proposal is being prepared and cannot be queued.
- submitted: the proposal is ready for intake validation.
- intake_review: reviewers are checking required fields and duplicate status.
- evidence_required: required evidence is missing or stale.
- adr_required: an ADR dependency is missing.
- gate_required: a release or no-go gate dependency is missing.
- security_review_required: security review evidence is missing.
- architecture_review_required: architecture review evidence is missing.
- operator_review_required: operator review evidence is missing.
- queued_for_future_decision: planning evidence is present for later review, but implementation remains unapproved.
- rejected: the proposal failed intake or no-go review.
- expired: the proposal evidence is stale.
- revoked: the proposal was withdrawn or invalidated.
- implementation_unapproved: the proposal is explicitly blocked from implementation.

## Runtime And Approval Boundary

No state enables runtime or approves implementation. `queued_for_future_decision` is not approval. `implementation_unapproved` remains the terminal safety state until a future scoped task explicitly adds approval records, ADRs, gate evidence, no-go regression evidence, and verification.

## Forbidden State Transitions

The state machine forbids any transition that marks implementation approved, marks an approval queue item approved, bypasses the approval workflow, bypasses ADR dependency, bypasses gate dependency, creates a v0.2 tag, creates a release, enables production auth, enables connector runtime, enables operator write execution, enables module activation, enables external calls, stores credentials or tokens, enables sandbox execution, adds package files, adds migrations, or adds runtime API execution routes.
