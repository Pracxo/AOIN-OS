# v0.2 Approval Workflow Stabilization Gate

## Purpose

AION-123 stabilizes the v0.2 approval workflow and implementation request
intake boundary created by AION-122. The gate proves that future implementation
requests can be reviewed, rejected, expired, revoked, and audited while every
runtime implementation approval remains false.

## Scope

In scope:

- approval workflow stabilization evidence
- implementation request intake validation evidence
- approval decision record evidence
- approval expiry and revocation evidence
- dual-control review evidence
- implementation approval guard checks
- no-go regression evidence
- static read-only console preview data

Out of scope:

- v0.2 implementation
- runtime enablement
- v0.2 tag creation
- v0.2 release creation
- connector runtime, production auth, operator write execution, module
  activation, external calls, credential storage, token storage, sandbox
  execution, package files, migrations, runtime API execution routes, SDK
  resources, or CLI command implementations

## Required Prior Gates

The approval workflow stabilization gate depends on:

- AION-122 implementation kickoff boundary check
- AION-122 implementation kickoff freeze
- AION-122 implementation kickoff no-go regression
- AION-121 readiness final review
- AION-120 planning stabilization gate
- AION-119 planning charter check
- AION-118 post-v0.1 release candidate gate
- AION-117 platform integration checkpoint
- docs check
- final docs audit
- domain drift check
- boundary check

## Approval Workflow Evidence

The workflow evidence confirms that a future implementation request must name a
requester, reviewer, approver, security reviewer, architecture reviewer,
operator reviewer, scoped ADR, scoped gate, expiry, revocation path, and no-go
acknowledgement. Approval remains a recorded decision only; it does not execute
work or enable runtime by itself.

## Intake Validation Evidence

The intake model requires workstream classification, requested runtime
capability, risk statement, security impact, policy impact, audit/provenance
impact, rollback plan, ADR dependency, gate dependency, test evidence, rejection
conditions, and default approval status false.

## Decision Record Evidence

Decision record evidence maps the workstream to required ADRs, required gates,
reviewers, evidence links, approval status, runtime approval status, and release
blockers. A missing decision record blocks implementation.

## Expiry And Revocation Evidence

Every approval record must expire and can be revoked after failed evidence,
scope drift, reviewer rejection, no-go discovery, or changed risk posture.
Expired or revoked approval returns to not approved and requires refreshed
evidence before future implementation can be considered.

## Dual-Control Evidence

High-risk workstreams may require both security and architecture approval.
Dual-control review still does not execute tools, call services, approve
runtime, or create release artifacts.

## Implementation Approval Guard Checks

Required safe values:

- `runtime_implementation_approved=false`
- `backlog_implementation_items_approved=false`
- `approval_workflow_bypassed=false`
- `adr_dependency_bypassed=false`
- `gate_dependency_bypassed=false`
- `approval_expiry_bypassed=false`
- `approval_revocation_bypassed=false`
- `dual_control_bypassed=false`
- `operator_write_execution_approved=false`
- `connector_implementation_approved=false`
- `production_auth_approved=false`
- `module_activation_approved=false`
- `external_calls_approved=false`
- `credential_storage_approved=false`
- `token_storage_approved=false`
- `sandbox_execution_approved=false`

## No-Go Conditions

The stabilization gate fails if implementation approval is set true, backlog
implementation approval is set true, approval workflow is bypassed, ADR or gate
dependency is bypassed, approval expiry or revocation is bypassed, dual-control
is bypassed, runtime is enabled, external calls are enabled, credentials or
tokens are stored, sandbox execution is enabled, package files are added,
migrations are added, runtime API execution routes are added, or a v0.2 tag or
release is created.

## No v0.2 Tag Or Release

AION-123 explicitly creates no v0.2 tag and no release. It does not mutate,
move, delete, or recreate `aion-v0.1.0`.

## AION-124 Workstream Intake Dependency

AION-124 builds on this stabilization gate by requiring candidate workstreams
to cite approval record evidence, sequencing evidence, rejection rules, and
workstream intake no-go results before planning review. It does not approve
implementation, create a v0.2 tag, create a release, or enable runtime.
AION-125 consumes the approval workflow stabilization gate as prior evidence
for the pre-implementation master freeze. The workflow remains evidence-only:
approval workflow bypass, expiry bypass, revocation bypass, dual-control bypass,
and every implementation approval remain false.

AION-126 uses this workflow for proposal registry preview only. Approval queue
preview entries do not approve implementation. Approval queue item approval,
runtime implementation approval, backlog implementation approval, workstream
implementation approval, approval workflow bypass, approval record missing,
ADR dependency bypass, and gate dependency bypass remain false.
