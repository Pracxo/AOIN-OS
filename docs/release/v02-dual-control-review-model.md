# v0.2 Dual-Control Review Model

## Requester

The requester submits the implementation request and owns problem statement,
workstream classification, evidence links, rollback plan, and no-go
acknowledgement. The requester cannot approve their own request.

## Reviewer

The reviewer checks completeness, workstream scope, evidence freshness,
required fields, rejection conditions, and safe default values.

## Security Reviewer

The security reviewer checks authentication, credentials, tokens, external
calls, sandbox posture, code loading, privileged bypass risk, rollback safety,
and secret redaction.

## Architecture Reviewer

The architecture reviewer checks ADR dependency, gate dependency, boundary fit,
runtime route impact, SDK/CLI impact, package posture, migration posture, and
compatibility with the AION OS architecture.

## Operator Reviewer

The operator reviewer checks operational safety, audit/provenance visibility,
manual control points, dry-run evidence, rollback clarity, and static console
impact.

## Approver

The approver records the final decision after required reviewers complete
review. Approval is not execution and does not enable runtime by itself.

## Auditor

The auditor verifies decision evidence, expiry, revocation path, reviewer set,
no-go status, and release blocker posture.

## Conflict-Of-Interest Rule

The requester cannot be the sole reviewer or approver. A reviewer with direct
implementation ownership must disclose that relationship and require an
independent approval path.

## Dual-Control Option

High-risk workstreams may require both a security approver and an architecture
approver. Dual-control approval still remains a record only.

## Break-Glass Future-Only

Break-glass remains future-only and unapproved. No AION-123 artifact enables a
break-glass bypass, privileged bypass, approval bypass, runtime execution, or
release bypass.

## AION-124 Intake Requirement

AION-124 requires future workstream intake records to declare whether
dual-control review is required. Missing dual-control evidence rejects the
workstream and does not approve implementation.
