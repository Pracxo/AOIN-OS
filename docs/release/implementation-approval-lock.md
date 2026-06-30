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
