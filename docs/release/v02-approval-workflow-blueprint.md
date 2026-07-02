# v0.2 Approval Workflow Blueprint

## Purpose

This blueprint defines the review and approval workflow required before any
future v0.2 implementation workstream can begin.

## Requester Role

The requester states the workstream, problem, proposed change, requested
runtime capability, ADR dependency, gate dependency, test evidence, rollback
plan, and no-go acknowledgement. The requester cannot approve their own
request.

## Reviewer Role

The reviewer checks completeness, scope, current safe values, evidence links,
and whether the request stays within the declared workstream.

## Approver Role

The approver may only decide on a request after required reviewers complete
their checks. Approval is a record, not execution, and approval does not enable
runtime by itself.

## Security Reviewer Role

The security reviewer checks credential/token handling, external call posture,
sandbox posture, authentication posture, threat model deltas, and rollback
evidence. Security review must fail closed when evidence is missing.

## Architecture Reviewer Role

The architecture reviewer checks ADR scope, boundary fit, dependency impact,
runtime route impact, SDK/CLI impact, package and migration posture, and
compatibility with existing AION OS architecture.

## Operator Reviewer Role

The operator reviewer checks operational safety, audit/provenance visibility,
manual control points, operator console impact, rollback clarity, and whether
the workstream can be observed without enabling write execution.

## Evidence Required Before Approval

Required evidence:

- scoped ADR
- scoped gate script
- scoped no-go regression
- docs audit
- boundary check
- full repository check
- rollback plan
- audit/provenance impact note
- security evidence
- operator review evidence

## Dual-Control Option

High-risk workstreams may require two approvers: one architecture approver and
one security approver. Dual-control approval still does not execute work and
does not enable runtime by itself.

## Approval Expiry

Every approval record must include an expiry. Expired approval records return
to not approved and require fresh evidence before implementation can proceed.

## Approval Revocation

Approval can be revoked by security review, architecture review, operator
review, failed gate evidence, scope drift, or discovery of a no-go condition.

## Approval Does Not Execute

Approval records do not execute tools, do not execute action proposals, do not
execute write paths, do not hard-delete records, and do not register runtime
routes.

## Approval Does Not Enable Runtime By Itself

Approval records do not enable production auth, connector runtime, module
activation, external calls, credential storage, token storage, sandbox
execution, package dependency additions, migrations, SDK resources, or CLI
command implementations.

## No-Go Conditions

The workflow blocks approval when evidence is missing, approval workflow is
bypassed, ADR dependency is bypassed, gate dependency is bypassed, any
implementation approval is already true without a valid decision record, or any
runtime capability is enabled before explicit future implementation approval.

## AION-123 Stabilization

AION-123 freezes the blueprint into a stabilization gate. Future requests must
also prove intake validation, decision evidence, expiry and revocation
evidence, dual-control evidence where required, and no-go regression evidence.
Approval remains false by default and still does not execute work or enable
runtime by itself.
