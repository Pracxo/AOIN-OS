# v0.2 Runtime Approval Board Preview

## Purpose

AION-144 adds the v0.2 runtime approval board preview so future runtime
implementation candidates can be reviewed against approval docket evidence,
implementation decision records, approval vote records, and go/no-go ledger
entries before any implementation approval is considered.

## Scope

This document defines preview-only governance records. It does not approve
runtime implementation, does not enable runtime behavior, does not create a
release, and does not create a tag.

In scope:

- runtime approval board preview structure
- approval vote record guard fields
- implementation go/no-go ledger boundary fields
- reviewer evidence dependencies
- ADR and gate dependencies
- explicit no-go conditions for future runtime candidates

Out of scope:

- connector runtime enablement
- operator write execution
- production auth enablement
- module activation
- external calls
- credential or token storage
- sandbox execution
- runtime API execution routes
- SDK or CLI runtime command implementations
- package manager files
- migrations

## Required Prior Gates

AION-144 depends on these prior gates remaining passing and unapproved:

| Gate | Required script | Required state |
| --- | --- | --- |
| Approval docket final review | `./scripts/v02-approval-docket-final-review.sh` | `approval_docket_final_review_approval=false` |
| Runtime approval lock | `./scripts/v02-runtime-approval-lock-freeze.sh` | `runtime_approval_lock_release_approved=false` |
| Approval docket stabilization | `./scripts/v02-approval-docket-stabilization-gate.sh` | `approval_docket_stabilization_approval=false` |
| Implementation decision record freeze | `./scripts/v02-implementation-decision-record-freeze.sh` | `implementation_decision_record_approval=false` |
| Approval docket preview | `./scripts/v02-approval-docket-preview-check.sh` | `approval_docket_item_approved=false` |
| Decision package final review | `./scripts/v02-decision-package-final-review.sh` | `decision_package_approval=false` |
| Decision package stabilization | `./scripts/v02-decision-package-stabilization-gate.sh` | `approval_readiness_approved=false` |
| Review board stabilization | `./scripts/v02-review-board-stabilization-gate.sh` | `review_board_decision_approval=false` |
| Submission registry stabilization | `./scripts/v02-submission-registry-stabilization-gate.sh` | `submission_approval=false` |
| Request pack final review | `./scripts/v02-request-pack-final-review.sh` | `request_pack_approval=false` |
| Planning track closeout | `./scripts/v02-planning-track-closeout.sh` | `workstream_implementation_approved=false` |
| Final planning release gate | `./scripts/v02-final-planning-release-gate.sh` | `runtime_implementation_approved=false` |

## Runtime Approval Board Is Preview-Only

`v02_runtime_approval_board_preview_created=true` records that the board
preview exists. `runtime_approval_board_preview_only=true` records that the
board has no runtime authority in AION-144.

The preview can attach docket evidence, vote records, and go/no-go ledger
entries. It cannot approve, route, execute, activate, release, or bypass any
future implementation work.

## Runtime Approval Board Does Not Approve Implementation

The runtime approval board preview keeps every approval value false:

- `runtime_approval_board_decision_approved=false`
- `runtime_implementation_approved=false`
- `implementation_decision_record_approval=false`
- `approval_docket_item_approved=false`
- `decision_package_approval=false`
- `approval_readiness_approved=false`
- `review_board_decision_approval=false`
- `routing_decision_approval=false`
- `reviewer_signoff_implementation_approval=false`
- `v02_release_approved=false`

Any future implementation candidate remains blocked until explicit approval
records, a follow-up ADR, and release gate evidence are created in a later task.

## Runtime Approval Board Does Not Enable Runtime

AION-144 does not enable runtime behavior:

- `operator_write_execution_approved=false`
- `connector_implementation_approved=false`
- `production_auth_approved=false`
- `module_activation_approved=false`
- `external_calls_approved=false`
- `credential_storage_approved=false`
- `token_storage_approved=false`
- `sandbox_execution_approved=false`

The board preview does not add API routers, SDK resources, CLI command
implementations, provider SDKs, external network clients, package files, or
migrations.

## Required Approval Docket Fields

Approval docket evidence attached to the runtime approval board must expose:

- `approval_docket_preview_only=true`
- `approval_docket_item_approved=false`
- `approval_docket_final_review_approval=false`
- `approval_docket_stabilization_approval=false`
- `runtime_approval_review_approved=false`
- `runtime_approval_lock_release_approved=false`

Missing approval docket records block board review.

## Required Implementation Decision Record Fields

Implementation decision records attached to the board must expose:

- `implementation_decision_record_created=true`
- `implementation_decision_record_approval=false`
- `implementation_decision_record_closeout_approval=false`
- `runtime_decision_lock_release_approved=false`
- `runtime_decision_readiness_approved=false`

An implementation decision record cannot be used as approval in AION-144.

## Required Vote Record Fields

Approval vote records must expose:

- `approval_vote_record_created=true`
- `approval_vote_record_approval=false`
- `approval_vote_record_runtime_effect=false`
- `runtime_approval_board_decision_approved=false`

Vote records are evidence only. They cannot approve implementation and cannot
change runtime state.

## Required Go/No-Go Ledger Fields

The go/no-go ledger must expose:

- `go_no_go_ledger_created=true`
- `implementation_go_status=false`
- `implementation_no_go_status=true`
- `go_no_go_ledger_runtime_effect=false`
- `runtime_implementation_approved=false`

The ledger can record a blocked or no-go outcome only. No implementation
candidate is marked go in AION-144.

## Required Reviewer Evidence

Reviewer evidence attached to the preview must include:

- approval docket final review evidence
- approval docket stabilization evidence
- implementation decision record closeout evidence
- runtime approval lock evidence
- decision package final review evidence
- decision package stabilization evidence
- review board stabilization evidence
- submission registry stabilization evidence
- request pack final review evidence
- planning track closeout evidence
- final planning release gate evidence
- docs, boundary, no-domain-drift, and final-docs audit results

Reviewer sign-off remains evidence only:
`reviewer_signoff_implementation_approval=false`.

## Required ADR Dependency

ADR 0135 must be indexed before the runtime approval board preview is accepted:

- `docs/adr/0135-v02-runtime-approval-board-preview.md`
- `docs/adr/README.md`

Bypassing the ADR dependency is a no-go condition:
`adr_dependency_bypassed=false`.

## Required Gate Dependency

The AION-144 gate stack must remain passing before this preview can be used:

- `./scripts/v02-runtime-approval-board-preview-check.sh`
- `./scripts/v02-approval-vote-record-freeze.sh`
- `./scripts/v02-runtime-approval-board-no-go-regression.sh`

Bypassing the gate dependency is a no-go condition:
`gate_dependency_bypassed=false`.

## Release And Tag Boundary

AION-144 creates no v0.2 tag and no v0.2 release.

- `v02_tag_created=false`
- `v02_release_created=false`
- `v02_release_approved=false`

The frozen `aion-v0.1.0` tag remains untouched.

## AION-145 Stabilization Handoff

AION-145 consumes this preview as inherited evidence and stabilizes it without
granting runtime authority. Runtime approval board decision approval, runtime
approval board stabilization approval, approval vote record approval, approval
vote record runtime effect, implementation go status, go/no-go ledger runtime
effect, runtime approval lock release approval, runtime approval review
approval, and runtime implementation approval remain false.
