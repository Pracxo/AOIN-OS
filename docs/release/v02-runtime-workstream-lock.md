# v0.2 Runtime Workstream Lock

## Purpose

This lock records runtime workstreams that remain blocked after the AION-122
implementation kickoff boundary.

## Locked Values

- `production_auth_implementation_locked=true`
- `connector_runtime_implementation_locked=true`
- `operator_write_execution_locked=true`
- `module_activation_locked=true`
- `external_calls_locked=true`
- `credential_storage_locked=true`
- `token_storage_locked=true`
- `sandbox_execution_locked=true`
- `runtime_route_registration_locked=true`
- `package_dependency_additions_locked=true`
- `migrations_locked=true`

## Interpretation

Locked means a future request may describe the workstream, but it may not
implement runtime behavior until a scoped ADR, approval decision record, gate
evidence, security review, architecture review, and operator review all pass.

## Current Approval State

All implementation approval fields remain false. AION-122 creates no approval
record that unlocks implementation.

## No-Go Handling

If any locked workstream is enabled before explicit future approval, the
implementation kickoff no-go regression must fail.

## AION-123 Approval Workflow Lock

AION-123 adds workflow-level locks for approval expiry, approval revocation,
and dual-control review. Locked workstreams remain blocked when approval
workflow bypass, ADR dependency bypass, gate dependency bypass, approval expiry
bypass, approval revocation bypass, or dual-control bypass is detected.
