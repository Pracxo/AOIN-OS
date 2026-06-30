# Module Activation Pre-Gate

## Purpose

The module activation pre-gate defines the minimum evidence required before a
future task can begin activation implementation. Passing this gate does not
activate modules. It only permits a later architecture review to consider an
implementation plan.

## Required Checks Before Future Activation Work

Before future activation work starts, these checks must pass locally:

- `./scripts/module-activation-design-review.sh`
- `./scripts/module-activation-no-go-regression.sh`
- `./scripts/module-pack-check.sh`
- `./scripts/generic-knowledge-demo.sh --offline-ok --skip-api`
- `./scripts/module-lifecycle-dashboard-check.sh`
- `./scripts/operator-platform-freeze-gate.sh`
- `./scripts/ui-release-gate.sh`
- `./scripts/docs-check.sh`
- `./scripts/final-docs-audit.sh`
- `./scripts/verify-no-domain-drift.sh`
- `./scripts/boundary-check.sh`
- `./scripts/check.sh`

## Required ADRs

Future activation implementation requires explicit ADR coverage for:

- activation runtime boundary
- sandbox execution model
- package trust and signed package model
- dependency policy
- runtime registration model
- operator approval and revocation model
- audit and provenance model
- rollback and disable model
- release gate and freeze posture

## Required Threat Model

The future threat model must cover:

- malicious module manifests
- executable payload smuggling
- dependency confusion
- package tampering
- sandbox escape
- policy bypass
- audit bypass
- route registration abuse
- capability activation abuse
- controlled execution abuse
- rollback failure

## Required Sandbox Design

The sandbox design must define file access, network posture, process limits,
resource limits, secret boundaries, provenance capture, audit events, package
entrypoints, allowed runtime adapters, and operator-visible failure behavior.

## Required Policy Model

The policy model must define generic permissions for activation request,
approval, runtime registration, capability invocation, module disable, rollback,
and audit review. Policy denial must remain authoritative over operator intent.

## Required Rollback Design

The rollback design must define how to disable future routing, revoke active
bindings, stop future invocations, retain audit/provenance records, preserve
review history, and avoid hard delete.

## Required Operator Approval Model

Operator approval must be explicit, scoped, revocable, auditable, and separate
from runtime execution. Approval must not bypass policy, sandbox limits,
production auth, release gates, or safety blockers.

## Required Audit/Provenance Design

Audit and provenance must record actor, scope, manifest hash, package identity,
binding identity, policy decision, sandbox posture, runtime registration
decision, invocation intent, rollback action, and redacted evidence references.

## Required Release Gate

The release gate must prove:

- activation remains disabled unless explicitly enabled by the future ADR
- package installation cannot occur outside the trust model
- code loading cannot occur outside the sandbox model
- runtime route registration is reviewed and reversible
- capability activation is policy-gated
- rollback and disable are tested
- no domain module logic enters Brain core

## No-Go Conditions

Future activation work cannot proceed if any of the following appears before
the required ADR and pre-gate evidence:

- code loader added
- package installer added
- dynamic module import added
- runtime route registration added
- capability activation enabled
- external dependency download added
- executable payload accepted
- controlled execution enabled
- module writes enabled
- `activation_ready=true` by default
- policy bypass
- audit bypass

## AION-117 Platform Integration Requirement

AION-117 adds `./scripts/platform-integration-checkpoint.sh`,
`./scripts/platform-integration-freeze-check.sh`, and
`./scripts/platform-integration-no-go-regression.sh` as required cross-phase
evidence before any module activation implementation ADR can be reviewed.
Module activation, code loading, runtime registration, capability activation,
controlled execution, package installation, external dependency downloads,
package files, migrations, API routes, SDK resources, and CLI implementations
remain blocked.
