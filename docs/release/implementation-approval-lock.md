# Implementation Approval Lock

## Locked State

The AION-118 release candidate baseline requires these values:

- `operator_write_execution_approved=false`
- `connector_implementation_approved=false`
- `production_auth_approved=false`
- `module_activation_approved=false`
- `external_calls_approved=false`
- `credential_storage_approved=false`
- `token_storage_approved=false`
- `sandbox_execution_approved=false`
- `v02_release_approved=false`

## Interpretation

Any future change that sets one of these values true is implementation approval
drift. It must be blocked unless a later task explicitly widens scope with an
ADR, implementation gate, no-go regression, and full verification evidence.

## Release Candidate Lock

The lock is evidence-only. It does not create a v0.2 tag, does not create a
release, and does not move, delete, or recreate `aion-v0.1.0`.

## AION-119 Planning Lock

AION-119 adds `runtime_implementation_approved=false` and
`v02_release_created=false` to the planning evidence. Future v0.2 backlog
items must reference this lock and cannot change approval state without a
future explicit ADR and gate evidence.

## AION-121 Final Readiness Lock

AION-121 adds `backlog_implementation_items_approved=false` to the final
readiness guard and reaffirms every implementation approval value as false.
The final readiness review is evidence-only and cannot be used to approve
runtime work, a v0.2 tag, or a v0.2 release.

## AION-122 Implementation Kickoff Lock

AION-122 adds approval workflow boundary evidence while preserving every lock.
`approval_workflow_bypassed=false`, `adr_dependency_bypassed=false`, and
`gate_dependency_bypassed=false` must remain false. The kickoff boundary
cannot approve runtime work, backlog implementation items, a v0.2 tag, or a
v0.2 release.

## AION-125 Pre-Implementation Master Lock

AION-125 adds the final master-freeze lock while preserving every approval
value. `workstream_implementation_approved=false`,
`approval_record_missing=false`, `approval_expiry_bypassed=false`,
`approval_revocation_bypassed=false`, and `dual_control_bypassed=false` must
remain false. The master freeze cannot approve runtime work, backlog
implementation items, workstream implementation items, a v0.2 tag, or a v0.2
release.
