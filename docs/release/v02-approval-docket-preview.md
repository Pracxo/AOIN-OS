# v0.2 Approval Docket Preview

## Purpose
AION-141 creates the v0.2 approval docket preview so future implementation decision records can be docketed before approval is considered. The docket records required evidence, dependencies, review states, and blockers without approving any runtime or implementation work.

## Scope
This preview covers documentation, synthetic examples, static console evidence, local guard scripts, and regression tests. It does not add runtime behavior, API routes, SDK resources, CLI commands, migrations, package files, network clients, external calls, credentials, tokens, sandbox execution, module activation, capability activation, code loading, runtime registration, tool execution, action proposal execution, write execution, hard deletes, or release automation.

## Approval Docket Is Preview-Only
The approval docket is preview-only. `v02_approval_docket_preview_created=true` and `approval_docket_preview_only=true` only mean that docket evidence exists for future review.

## Approval Docket Does Not Approve Implementation
Approval docket presence does not approve implementation. `approval_docket_item_approved=false`, `implementation_decision_record_approval=false`, `runtime_approval_review_approved=false`, `runtime_implementation_approved=false`, and `decision_package_approval=false`.

## Approval Docket Does Not Enable Runtime
Approval docket completeness does not enable runtime. `runtime_decision_lock_release_approved=false`, `runtime_decision_readiness_approved=false`, `operator_write_execution_approved=false`, `connector_implementation_approved=false`, `production_auth_approved=false`, `module_activation_approved=false`, `external_calls_approved=false`, `credential_storage_approved=false`, `token_storage_approved=false`, and `sandbox_execution_approved=false`.

## Required Decision Package Fields
- `decision_package_preview_only=true`
- `decision_package_approval=false`
- `approval_readiness_preview_only=true`
- `approval_readiness_approved=false`
- `runtime_decision_lock_created=true`
- `runtime_decision_lock_release_approved=false`
- `runtime_decision_readiness_approved=false`
- `review_board_decision_approval=false`
- `routing_decision_approval=false`
- `reviewer_signoff_implementation_approval=false`

## Required Decision Record Fields
- `implementation_decision_record_created=true`
- `implementation_decision_record_approval=false`
- `approval_docket_item_approved=false`
- `runtime_approval_review_approved=false`
- `runtime_implementation_approved=false`
- `approval_record_missing=false`
- `adr_dependency_bypassed=false`
- `gate_dependency_bypassed=false`
- `evidence_completeness_bypassed=false`

## Required Reviewer Evidence
Reviewer evidence must identify the reviewer role, reviewed decision package, reviewed implementation decision record, required ADR, required gate, expected safe value, unresolved blocker, and approval state. Reviewer evidence is not implementation approval and reviewer sign-off implementation approval remains false.

## Required ADR Dependency
Every docketed implementation decision record must reference the ADR that defines its approval boundary. ADR dependency presence is not runtime enablement and `adr_dependency_bypassed=false`.

## Required Gate Dependency
Every docketed implementation decision record must reference the local gate or freeze script that proves the boundary remains locked. Gate dependency success is not runtime enablement and `gate_dependency_bypassed=false`.

## Docket States
- `drafted`
- `docketed`
- `evidence_attached`
- `decision_record_attached`
- `review_ready_preview`
- `runtime_review_pending`
- `blocked`
- `rejected`
- `expired`
- `revoked`
- `docket_unapproved`
- `implementation_unapproved`

No docket state approves implementation or enables runtime.

## Release Statement
AION-141 creates no v0.2 tag and no v0.2 release. The v0.1 release baseline remains frozen and the `aion-v0.1.0` tag must not be moved, deleted, or recreated.

## AION-142 Stabilization Handoff
AION-142 stabilizes this approval docket preview as evidence only. Approval docket stabilization approval, approval docket item approval, implementation decision record freeze approval, implementation decision record approval, runtime approval review approval, runtime decision lock release approval, and runtime implementation approval remain false.
