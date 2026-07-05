# v0.2 Decision Package Preview

## Purpose

AION-138 creates a decision package preview for the v0.2 planning track. It
consolidates review-board stabilization, submission routing, request-pack
evidence, proposal registry state, approval queue state, and runtime boundary
evidence into one approval-readiness bundle.

The package is preview-only. It prepares the evidence that a future explicit
approval workflow would need, but it does not approve the decision package or
approve runtime implementation.

## Scope

This milestone adds documentation, examples, static console demo data, local
shell gates, and tests only. It does not add runtime code, API routes, SDK
resources, CLI command implementations, package files, migrations, credentials,
tokens, external calls, sandbox execution, module activation, connector
activation, operator write execution, a v0.2 tag, or a v0.2 release.

## Required Prior Gates

- `./scripts/v02-review-board-stabilization-gate.sh`
- `./scripts/v02-review-routing-freeze.sh`
- `./scripts/v02-review-board-stabilization-no-go-regression.sh`
- `./scripts/v02-preapproval-review-board-check.sh`
- `./scripts/v02-submission-registry-stabilization-gate.sh`
- `./scripts/v02-submission-registry-preview-check.sh`
- `./scripts/v02-request-pack-final-review.sh`
- `./scripts/v02-request-pack-stabilization-gate.sh`
- `./scripts/v02-implementation-request-pack-check.sh`
- `./scripts/v02-planning-track-closeout.sh`
- `./scripts/v02-final-planning-release-gate.sh`
- `./scripts/docs-check.sh`
- `./scripts/final-docs-audit.sh`
- `./scripts/verify-no-domain-drift.sh`
- `./scripts/boundary-check.sh`

## Package Contents

- Decision package preview document.
- Approval readiness evidence bundle.
- Runtime decision boundary.
- Decision package state model.
- Evidence matrix.
- No-go condition register.
- Closeout checklist.
- ADR 0129.
- Synthetic JSON examples.
- Static console read-only demo data.
- Local preview, freeze, and no-go regression scripts.

## Approval Lock

- decision_package_approval=false
- approval_readiness_approved=false
- review_board_decision_approval=false
- routing_decision_approval=false
- reviewer_signoff_implementation_approval=false
- preapproval_queue_item_approved=false
- request_pack_approval=false
- submission_approval=false
- runtime_implementation_approved=false
- backlog_implementation_items_approved=false
- workstream_implementation_approved=false
- proposal_implementation_approved=false
- approval_queue_item_approved=false
- approval_workflow_bypassed=false

## Runtime Boundary

The decision package is an evidence bundle. It cannot start a runtime
implementation workstream, enable a connector, enable production auth, enable
module activation, execute an operator write path, store protected material,
open external calls, or enable sandbox execution.

## Static Console Evidence

The static console shows the package as read-only local demo data. The panels
are informational and expose no inputs, write controls, approval controls,
activation controls, package installation instructions, migration instructions,
or runtime execution paths.

## No-Go Conditions

The gate fails if any approval, bypass, release, tag, runtime, connector,
production auth, module activation, operator write execution, external call,
credential/token storage, sandbox execution, package, migration, API runtime,
SDK resource, CLI command, or domain implementation condition is present.

## Release Boundary

AION-138 creates no v0.2 tag and no v0.2 release. The frozen `aion-v0.1.0`
baseline remains untouched.

## AION-139 Stabilization Handoff

AION-139 stabilizes this preview into a decision package baseline and approval
readiness freeze. The handoff remains preview-only: decision package approval,
approval readiness approval, runtime decision readiness approval, review board
decision approval, routing decision approval, reviewer sign-off implementation
approval, submission approval, request pack approval, runtime implementation
approval, v0.2 tag creation, and v0.2 release creation all remain false or
absent.
