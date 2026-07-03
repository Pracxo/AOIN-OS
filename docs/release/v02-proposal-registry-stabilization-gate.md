# v0.2 Proposal Registry Stabilization Gate

## Purpose

AION-127 stabilizes the AION-126 proposal registry and approval queue preview before any v0.2 implementation approval is considered.

## Scope

This gate is planning-only. It covers documentation, synthetic examples, static console preview data, local scripts, and regression tests. It does not add runtime code, API routes, SDK resources, CLI commands, package files, migrations, external calls, credential storage, token storage, sandbox execution, production auth, connector runtime, operator write execution, module activation, capability activation, code loading, or runtime registration.

## Required Prior Gates

- `./scripts/v02-workstream-proposal-registry-check.sh`
- `./scripts/v02-proposal-registry-freeze.sh`
- `./scripts/v02-proposal-registry-no-go-regression.sh`
- `./scripts/v02-preimplementation-master-freeze.sh`
- `./scripts/v02-preimplementation-final-baseline-check.sh`
- `./scripts/v02-workstream-intake-readiness-gate.sh`
- `./scripts/v02-approval-workflow-stabilization-gate.sh`
- `./scripts/v02-implementation-kickoff-boundary-check.sh`
- `./scripts/v02-readiness-final-review.sh`

## Proposal Registry Evidence

The registry remains preview-only and read-only. It can list candidate workstream proposals, required ADRs, required gates, evidence gaps, blockers, and next planning actions, but it cannot approve implementation.

## Approval Queue Evidence

The approval queue remains preview-only. Approval queue items keep `approval_queue_item_approved=false`, and the queue does not create approval records, bypass review, or enable runtime work.

## Candidate Workstream Evidence

The candidate workstream baseline records production auth, audit/provenance hardening, rollback/recovery, external call release gate, connector runtime, credential store, sandbox runtime, operator write execution, module activation, and production UI decision proposals with approval and implementation status locked false.

## Lifecycle Evidence

Every lifecycle state maps to required evidence, reviewers, allowed-today status, implementation approved false, runtime enabled false, and release blockers.

## Approval Lock Checks

The gate fails if proposal, queue, workstream, backlog, runtime, operator write, connector, production auth, module activation, external call, credential, token, sandbox, package, migration, API runtime route, SDK resource, CLI command, or frontend dependency approval is set true.

## No-Go Conditions

No-go conditions include approval queue item approved true, proposal state implies implementation approved, implementation approval set true, workstream implementation approval set true, backlog implementation approval set true, approval workflow bypassed, approval record missing, ADR dependency bypassed, gate dependency bypassed, approval expiry bypassed, approval revocation bypassed, dual-control bypassed, v0.2 tag created, v0.2 release created, production auth enabled, connector runtime enabled, operator write execution enabled, module activation enabled, external calls enabled, credential/token storage enabled, sandbox execution enabled, package files added, migrations added, and runtime API execution routes added.

## No v0.2 Tag Or Release

AION-127 explicitly creates no v0.2 tag and no release. The `aion-v0.1.0` tag remains the frozen release baseline.

## AION-128 Planning Master Checkpoint

AION-128 consumes this stabilization gate as an inherited planning baseline.
The proposal registry remains preview-only, the approval queue remains
preview-only, approval queue item approval remains false, proposal
implementation approval remains false, runtime implementation approval remains
false, and no v0.2 tag or release is created.
