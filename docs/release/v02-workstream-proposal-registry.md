# v0.2 Workstream Proposal Registry

## Purpose

AION-126 adds a v0.2 workstream proposal registry on top of the AION-125 pre-implementation master freeze. The registry gives future implementation workstreams a catalog, review, and queue surface without approving or starting implementation.

## Scope

This registry is planning-only. It covers documentation, synthetic examples, static console preview data, local scripts, and regression tests. It does not add runtime code, API routes, SDK resources, CLI commands, package files, migrations, network clients, external calls, credential storage, token storage, sandbox execution, production auth, connector runtime, operator write execution, module activation, code loading, runtime registration, or capability activation.

## Registry Rules

- Every proposal must have a stable request ID and workstream name.
- Every proposal must enter with approval status default false.
- Every proposal must enter with implementation status default false.
- Every proposal must cite an ADR dependency.
- Every proposal must cite a release or safety gate dependency.
- Every proposal must carry evidence before it can be queued for future decision.
- The registry may list, reject, expire, revoke, or queue proposals, but it must not approve implementation.
- The registry must keep `proposal_registry_preview_only=true`.

## Allowed Proposal States

- drafted
- submitted
- intake_review
- evidence_required
- adr_required
- gate_required
- security_review_required
- architecture_review_required
- operator_review_required
- queued_for_future_decision
- rejected
- expired
- revoked
- implementation_unapproved

No state enables runtime, approves implementation, creates a tag, creates a release, or mutates the v0.1 release baseline.

## Required Proposal Fields

- request ID
- workstream
- requested capability
- status
- implementation approved flag
- approval status flag
- required ADR
- required gate
- required evidence
- blocker
- next planning action
- no-go acknowledgement

## Required Evidence

Each proposal must include a problem statement, risk statement, security impact, architecture impact, policy impact, audit/provenance impact, rollback plan, ADR dependency, gate dependency, test evidence, and no-go acknowledgement.

## Required ADR Dependency

Every proposal must point to a future ADR before implementation can be considered. A missing ADR dependency moves the proposal to `adr_required` or rejection and keeps implementation unapproved.

## Required Gate Dependency

Every proposal must point to a future gate or no-go regression before implementation can be considered. A missing gate dependency moves the proposal to `gate_required` or rejection and keeps implementation unapproved.

## Approval Status Default False

Proposal approval defaults to false. Approval queue preview records are not approval records and cannot set approval true.

## Implementation Status Default False

Implementation status defaults to false for every proposal. A queued proposal remains `implementation_unapproved` until a later scoped implementation task explicitly widens scope with approval records, ADRs, gate evidence, and no-go regression evidence.

## No-Go Conditions

The registry fails if implementation approval is set true, workstream implementation approval is set true, a proposal state implies implementation approved, an approval queue item is marked approved, the approval workflow is bypassed, an approval record is missing, ADR dependency is bypassed, gate dependency is bypassed, a v0.2 tag is created, a v0.2 release is created, production auth is enabled, connector runtime is enabled, operator write execution is enabled, module activation is enabled, external calls are enabled, credential or token storage is enabled, sandbox execution is enabled, package files are added, migrations are added, or runtime API execution routes are added.

## No v0.2 Tag Or Release

AION-126 explicitly creates no v0.2 tag and no release. `aion-v0.1.0` remains the frozen release baseline.
