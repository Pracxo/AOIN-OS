# v0.2 Proposal Review Rules

## Intake Validation

Intake validation checks that each proposal has a request ID, workstream, requested capability, status, blocker, next planning action, required ADR, required gate, required evidence, and no-go acknowledgement.

## Duplicate Proposal Handling

Duplicate proposals are merged only as planning records. Duplicate handling cannot approve implementation, bypass evidence, or collapse dual-control review.

## Missing Evidence Rejection

A proposal with missing problem statement, risk statement, security impact, architecture impact, policy impact, audit/provenance impact, rollback plan, ADR dependency, gate dependency, test evidence, or no-go acknowledgement is rejected or moved to evidence required.

## Unsupported Runtime Capability Rejection

Requests that try to enable runtime capabilities directly are rejected. This includes production auth, connector runtime, operator write execution, module activation, external calls, credential storage, token storage, sandbox execution, code loading, runtime registration, capability activation, package files, migrations, and runtime API execution routes.

## Security Review Requirement

Security review is required before a future approval can be considered. Security review absence keeps the proposal unapproved.

## Architecture Review Requirement

Architecture review is required before a future approval can be considered. Architecture review absence keeps the proposal unapproved.

## Operator Review Requirement

Operator review is required before a future approval can be considered. Operator review absence keeps the proposal unapproved.

## Rollback/Audit Requirement

Rollback and audit/provenance evidence are required before a future approval can be considered. Missing rollback or audit evidence keeps the proposal unapproved.

## ADR And Gate Dependency Requirement

Every proposal must cite a future ADR and a future gate. ADR dependency bypass and gate dependency bypass are no-go conditions.

## No Direct Implementation Approval

The registry, index, and queue preview cannot approve implementation directly. Runtime implementation approval, backlog implementation approval, workstream implementation approval, approval queue item approval, and v0.2 release approval remain false.

## AION-127 Stabilization Rules

AION-127 adds stabilization review for candidate workstream evidence,
lifecycle evidence, closeout evidence, expiry, revocation, and dual-control
status. The review still cannot approve implementation. Proposal
implementation approval, approval queue item approval, runtime implementation
approval, backlog implementation approval, workstream implementation approval,
and v0.2 release approval remain false.
