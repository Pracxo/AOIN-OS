# v0.2 Submission Registry Preview

## Purpose

AION-134 creates the v0.2 submission registry preview so future request
candidates can be catalogued before approval review. The registry records
required evidence, ADR dependencies, gate dependencies, reviewer evidence, and
blocked approval states without creating an implementation approval.

## Scope

This artifact is planning-only. It covers release docs, synthetic examples,
static console preview data, local guard scripts, and tests. It does not enable
runtime behavior, API routes, SDK resources, CLI command implementations,
package files, migrations, connector runtime, operator write execution, module
activation, production auth, sandbox execution, external calls, credential
storage, token storage, code loading, runtime registration, or capability
activation.

## Registry Preview Rules

- Registry records are preview-only and cannot be treated as approval records.
- Every candidate must keep `submission_approval=false`.
- Every candidate must keep `implementation_approval=false`.
- Every candidate must include an ADR dependency and gate dependency.
- Every candidate must include reviewer evidence before any future approval
  review.
- The registry may describe blockers and next planning action only.
- Missing evidence blocks advancement and does not create an approval bypass.

## Required Submission Fields

- Candidate ID
- Workstream
- Submission status
- Submission approval default false
- Implementation approval default false
- Request pack reference
- Pre-approval queue state
- Blocker
- Next planning action

## Required Evidence Fields

- Problem evidence
- Risk evidence
- Security evidence
- Architecture evidence
- Policy evidence
- Audit/provenance evidence
- Rollback or recovery evidence
- Test evidence
- No-go acknowledgement

## Required ADR Dependency

Each submission registry record must name a future ADR dependency. ADR presence
is review evidence only and does not approve implementation.

## Required Gate Dependency

Each submission registry record must name a future gate dependency. Gate success
is review evidence only and does not approve implementation or runtime.

## Required Reviewer Evidence

Required reviewer evidence includes architecture, security, policy,
operator/platform, audit/provenance, and release governance review notes. Those
notes must remain non-executing and cannot replace explicit approval records.

## Approval Defaults

Submission approval default false is mandatory. Implementation approval default
false is mandatory. Request pack approval, pre-approval queue item approval,
approval queue item approval, proposal implementation approval, workstream
implementation approval, backlog implementation approval, runtime
implementation approval, and release approval remain false.

## No v0.2 Tag Or Release

AION-134 explicitly creates no v0.2 tag and no v0.2 release. The
`aion-v0.1.0` tag remains frozen and must not be moved, deleted, recreated, or
retagged.

## AION-135 Stabilization Handoff

AION-135 stabilizes this preview into a controlled pre-approval queue baseline.
The handoff keeps the submission registry preview-only, keeps preapproval
queue item approval false, keeps request pack approval false, keeps submission
approval false, keeps implementation approvals false, and creates no v0.2 tag
or release.

AION-136 preserves the same preview-only registry posture while adding
review-board routing. Routing readiness is not submission approval,
implementation approval, runtime enablement, tag creation, or release creation.
