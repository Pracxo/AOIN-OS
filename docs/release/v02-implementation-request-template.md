# v0.2 Implementation Request Template

## Workstream

Name exactly one workstream.

## Problem Statement

Describe the problem the workstream is intended to solve.

## Proposed Change

Describe the proposed implementation boundary without enabling runtime work in
the request itself.

## Runtime Capability Requested

Name the runtime capability requested. Default: not approved.

## Security Impact

Describe credential, token, external call, sandbox, authentication, and
authorization impact.

## Policy Impact

Describe policy checks, no-go checks, approval checks, and bypass prevention.

## Audit/Provenance Impact

Describe audit events, provenance records, traceability, and review evidence.

## Rollback Plan

Describe how the change can be reverted or disabled if approved in a future
implementation task.

## ADR Dependency

Name the required scoped ADR. Default: not satisfied.

## Gate Dependency

Name the required scoped gate and no-go regression. Default: not satisfied.

## Test Evidence

List required tests and scripts. Default: no evidence accepted until the future
task provides it.

## No-Go Acknowledgement

The requester acknowledges that v0.2 tag creation, release creation, runtime
enablement, external calls, credentials, tokens, sandbox execution, package
files, migrations, API runtime routes, SDK resources, and CLI command
implementations remain blocked until explicit future approval.

## Approval Status

Default approval status: false.

- `runtime_implementation_approved=false`
- `backlog_implementation_items_approved=false`
- `approval_workflow_bypassed=false`
- `adr_dependency_bypassed=false`
- `gate_dependency_bypassed=false`

## AION-123 Intake Stabilization

AION-123 requires each future implementation request to include risk statement,
security impact, policy impact, audit/provenance impact, rollback plan, ADR
dependency, gate dependency, test evidence, expiry handling, revocation
handling, and dual-control status where required. Missing fields reject the
request by default.
