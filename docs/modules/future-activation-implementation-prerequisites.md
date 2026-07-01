# Future Activation Implementation Prerequisites

## Purpose

This document defines the prerequisites for any future task that proposes real
module activation. AION-105 does not satisfy these prerequisites; it only
defines them.

## Activation Threat Model

Future work must define threats for malicious manifests, executable payloads,
dependency substitution, package tampering, sandbox escape, route registration
abuse, policy bypass, audit bypass, operator approval abuse, rollback failure,
and module deactivation failure.

## Sandbox Design

Future work must define a sandbox boundary before code can load. The sandbox
must cover file access, network posture, execution limits, resource limits,
secret isolation, observable events, deterministic failure records, and
operator-visible status.

## Package Trust Model

Future work must define trusted package identity, provenance, manifest hash,
source attestations, allowed package formats, review records, package
immutability, and revocation behavior.

## Signed Package Design

Future work must define signing requirements, signature verification,
certificate or key lifecycle, trust roots, revocation, tamper evidence, and
release gate checks.

## Dependency Policy

Future work must define which dependencies are allowed, how dependency drift is
reviewed, how dependency metadata is recorded, and how external dependency
fetches are blocked unless explicitly approved.

## Rollback/Disable Design

Future work must define how to disable activation, revoke active bindings,
stop future routing, stop future invocation, preserve audit/provenance, and
avoid hard delete.

## Runtime Registration Design

Future work must define API route registration boundaries, SDK/CLI exposure
rules, policy action rules, reverse migration behavior, and operator-visible
registration state.

## Operator Approval Model

Future work must define scoped approvals, revocation, separation from
execution, approval expiry, approval evidence, and denial behavior.

## Production Auth Dependency

Future activation must depend on a production auth architecture that is already
approved and implemented. Local auth prototypes and mock claims are not enough
to authorize real module activation.

## Connector Boundary Dependency

Future module activation that depends on external connectors must also pass the
AION-106 connector boundary gate. Connector runtime, external calls, connector
SDK dependencies, provider SDK dependencies, credentials, token storage,
dynamic routes, and connector activation must remain disabled until a future
connector ADR, threat model, credential boundary, egress guard, ingress guard,
policy catalogue, dry-run simulator, disabled prototype, release gate, and
rollback plan are approved.

## Release Gate Dependency

Future activation must have release and freeze gates that fail closed on code
loading, package installation, dynamic route registration, capability
activation, controlled execution, policy bypass, audit bypass, and rollback
failure.

## Minimum Test Matrix

The minimum test matrix must include:

- manifest validation
- package signature validation
- dependency policy denial
- sandbox denial
- policy denial
- operator approval denial
- runtime registration denial
- activation denial
- capability invocation denial
- rollback and disable
- audit/provenance recording
- no-domain-drift
- boundary check
- full repository health check

## AION-119 Planning Charter Requirement

AION-119 adds the v0.2 planning charter before any module activation
implementation proposal. Future activation remains planning-only until a
scoped ADR, activation gate, sandbox dependency, package trust model,
rollback/audit evidence, operator review model, and no-go regression pass.
Code loading, runtime registration, capability activation, package
installation, external dependency download, and module writes remain disabled.

## AION-120 Planning Stabilization Dependency

AION-120 adds the v0.2 planning stabilization gate and blocked work register as
additional prerequisites before any module activation implementation proposal.
Code loading, runtime registration, capability activation, package
installation, controlled execution, external dependency download, module
writes, and backlog implementation approval remain blocked.

## AION-121 Readiness Final Review Dependency

AION-121 adds the v0.2 readiness final review and blocked implementation
summary as additional prerequisites before any module activation implementation
proposal. Code loading, runtime registration, capability activation, package
installation, controlled execution, external dependency download, module
writes, and backlog implementation approval remain blocked until future scoped
ADR, gate, security, rollback, audit/provenance, operator review, and no-go
evidence pass.

## AION-122 Implementation Kickoff Boundary Dependency

AION-122 adds the v0.2 implementation kickoff boundary and runtime workstream
lock as additional prerequisites before any module activation implementation
proposal. Code loading, runtime registration, capability activation, package
installation, controlled execution, external dependency download, module
writes, approval workflow bypass, ADR dependency bypass, gate dependency
bypass, and backlog implementation approval remain blocked until future scoped
request, approval decision record, ADR, gate, security, rollback,
audit/provenance, operator review, and no-go evidence pass.
