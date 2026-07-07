# v0.2 Submission Registry Stabilization Gate

## Purpose

Stabilize the AION-134 submission registry preview into a controlled
pre-approval queue baseline. This gate records the request candidate closeout
state while keeping all submission, request, proposal, workstream, backlog, and
runtime approvals locked to false.

## Scope

This is planning and evidence stabilization only. It does not approve
implementation, does not enable runtime, does not execute tools, does not add
network clients, and does not create a release artifact.

## Required Prior Gates

- v0.2 submission registry preview check
- v0.2 pre-approval queue freeze
- v0.2 pre-approval queue no-go regression
- v0.2 request pack final review
- v0.2 request pack stabilization gate
- v0.2 implementation request pack check
- v0.2 planning track closeout
- v0.2 final planning release gate

## Submission Registry Evidence

The registry remains preview-only. Each entry must identify a candidate,
workstream, required ADR, required gate, evidence bundle, blocker, and next
planning action. Submission approval remains false for every candidate.

## Pre-Approval Queue Evidence

The queue remains preview-only. Pre-approval queue item approval remains false,
submission approval remains false, request pack approval remains false, and no
implementation approval may be inferred from queue placement.

## Request Candidate Evidence

Request candidates are closed out as planning records only. Candidate records
must keep implementation approval false, runtime implementation approval false,
and workstream implementation approval false.

## Submission Lifecycle Evidence

Lifecycle states may move through intake, evidence review, ADR review, gate
review, rejection, expiry, or revocation. No lifecycle state approves
submission, approves implementation, enables runtime, or creates a release.

## Approval Lock Checks

- preapproval_queue_item_approved=false
- submission_approval=false
- request_pack_approval=false
- approval_queue_item_approved=false
- proposal_implementation_approved=false
- workstream_implementation_approved=false
- runtime_implementation_approved=false
- backlog_implementation_items_approved=false

## No-Go Conditions

The gate fails if any approval lock is true, if an approval workflow is
bypassed, if an approval record is missing, if ADR or gate dependencies are
bypassed, if external calls or credentials are introduced, if sandbox execution
is enabled, if package files or migrations are added, or if runtime API
execution routes are added.

## No Tag Or Release

AION-135 explicitly creates no v0.2 tag and no v0.2 release. The
`aion-v0.1.0` baseline remains frozen and untouched.

## AION-136 Review Board Handoff

AION-136 consumes this stabilized registry as evidence for pre-approval review
board routing. Routing readiness remains planning-only: review board decision
approval, submission approval, request pack approval, preapproval queue item
approval, implementation approval, runtime enablement, v0.2 tag creation, and
v0.2 release creation all remain false or absent.

## AION-137 Review Board Stabilization Handoff

AION-137 consumes this stabilized registry as inherited evidence for review
board stabilization. Submission registry stabilization remains preview-only;
routing decision approval, reviewer sign-off implementation approval,
submission approval, request pack approval, preapproval queue item approval,
implementation approval, runtime enablement, v0.2 tag creation, and v0.2
release creation all remain false or absent.

## AION-138 Decision Package Handoff

AION-138 consumes this stabilized registry as inherited decision package
evidence. Submission registry stabilization remains preview-only; decision
package approval, approval readiness approval, routing decision approval,
reviewer sign-off implementation approval, submission approval, request pack
approval, preapproval queue item approval, implementation approval, runtime
enablement, v0.2 tag creation, and v0.2 release creation all remain false or
absent.

AION-139 consumes submission registry stabilization as inherited evidence for
decision package stabilization only. Runtime decision readiness approval,
decision package approval, approval readiness approval, submission approval,
request pack approval, preapproval queue item approval, and runtime
implementation approval remain false.

## AION-145 Runtime Approval Board Stabilization Handoff

AION-145 consumes submission registry stabilization as inherited evidence only.
Submission approval, request pack approval, preapproval queue item approval,
runtime approval board stabilization approval, runtime approval board decision
approval, approval vote record approval, approval vote record runtime effect,
implementation go status, and runtime implementation approval remain false.
