# v0.2 Workstream Intake Readiness Gate

## Purpose

AION-124 defines the gate for accepting candidate v0.2 workstreams into planning review. The gate proves that intake evidence, approval record evidence, sequencing evidence, and rejection evidence are present before any future implementation request can be considered.

## Scope

This gate is planning-only. It covers docs, synthetic examples, static console preview data, scripts, and regression tests. It does not add runtime code, API routes, SDK resources, CLI commands, package files, migrations, external calls, credential storage, token storage, sandbox execution, or write execution.

## Required Prior Gates

- `./scripts/v02-approval-workflow-stabilization-gate.sh`
- `./scripts/v02-approval-workflow-freeze.sh`
- `./scripts/v02-approval-workflow-no-go-regression.sh`
- `./scripts/v02-implementation-kickoff-boundary-check.sh`
- `./scripts/v02-readiness-final-review.sh`
- `./scripts/v02-planning-stabilization-gate.sh`
- `./scripts/v02-planning-charter-check.sh`
- `./scripts/post-v01-release-candidate-gate.sh`
- `./scripts/platform-integration-checkpoint.sh`
- `./scripts/docs-check.sh`
- `./scripts/final-docs-audit.sh`
- `./scripts/verify-no-domain-drift.sh`
- `./scripts/boundary-check.sh`

## Workstream Intake Evidence

Every candidate workstream must provide the workstream name, problem statement, risk statement, security impact, policy impact, rollback/audit consideration, ADR dependency, gate dependency, test evidence, and the requested runtime capability. Missing intake evidence rejects the workstream before planning.

## Approval Record Evidence

Every candidate must point to an approval record evidence pack with ADR evidence, gate evidence, security review evidence, architecture review evidence, operator review evidence, rollback/audit evidence, expiry status, revocation path, and no-go result. Default approval status is false.

## Sequencing Evidence

Sequencing records are planning-only. They order future workstream review without approving implementation. Production auth remains the first candidate planning dependency; audit/provenance hardening and rollback/recovery remain planning-only; connector runtime, credential store, sandbox runtime, operator write execution, and module activation remain locked.

## Rejection Evidence

Rejected workstreams must record the rejection rule, missing evidence, reviewer note, and next planning action. Direct implementation approval requests, runtime enablement without ADRs, external calls without release gates, credential/token storage without credential store ADRs, sandbox execution without sandbox ADRs, package files, migrations, and runtime routes are no-go conditions.

## Implementation Approval Guard Checks

- `runtime_implementation_approved=false`
- `backlog_implementation_items_approved=false`
- `workstream_implementation_approved=false`
- `approval_workflow_bypassed=false`
- `approval_record_missing=false`
- `adr_dependency_bypassed=false`
- `gate_dependency_bypassed=false`
- `approval_expiry_bypassed=false`
- `approval_revocation_bypassed=false`
- `dual_control_bypassed=false`

## No-Go Conditions

The gate fails if implementation approval is set true, backlog implementation approval is set true, a workstream is marked implementation approved, the approval workflow is bypassed, an approval record is missing, ADR or gate dependencies are bypassed, expiry or revocation is bypassed, dual-control is bypassed, v0.2 tag or release markers exist, runtime capabilities are enabled, external calls are added, credentials/tokens are stored, sandbox execution is enabled, package files are added, migrations are added, or runtime API execution routes are added.

## No v0.2 Tag Or Release

AION-124 explicitly creates no v0.2 tag and no release. `aion-v0.1.0` remains the frozen release baseline.

## AION-125 Master Freeze Dependency

AION-125 consumes this intake gate as a required prior gate for the final
pre-implementation master freeze. Intake readiness remains planning-only and
does not approve runtime implementation, workstream implementation, a v0.2 tag,
or a v0.2 release.
