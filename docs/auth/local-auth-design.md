# Local Auth Design

## Purpose

AION-093 defines the local authentication and authorization design for the
future Operator Console. It gives the project an identity, session, role, and
access-control blueprint before any login system or production authentication
runtime exists.

## Current State

The current Operator Console work is local, static, and read-only unless an
existing Brain API exposes a governed dry-run record path. ActorContext remains
the current internal context mechanism. Policy remains authoritative for
backend access. Audit, approval, autonomy, redaction, and provenance gates
remain in force.

ActorContext remains the current internal context mechanism.
Policy remains authoritative.

## Why AION-093 Is Design-Only

AION-093 does not implement production auth.
no production auth is implemented.
No credentials are stored. No external identity provider is integrated. No
login endpoint is added. No passkey or WebAuthn runtime is added. No session
cookie, bearer credential, or browser storage mechanism is introduced.

The goal is to make later implementation work testable and bounded before any
auth runtime exists.

## Local-First Assumptions

- The static console remains a local design and preview surface.
- Demo identities are synthetic and must not be treated as production users.
- Local dev mode may supply ActorContext for internal Brain policy checks.
- Local access does not imply permission to execute, activate, load code,
  register routes, enable providers, or bypass policy.

## Identity Boundaries

A local operator identity is a structured description of an actor, workspace,
owner scope, and role labels. It is not proof of production identity. Future
production identity must bind actor identity to a reviewed identity provider
architecture, provisioning model, audit correlation model, and release gate.

## Session Boundaries

A future local session is a time-bounded browser-to-console boundary. AION-093
does not create real sessions. The static console has no authenticated session.
No cookies or tokens are implemented. Future session work must define timeout,
logout, rotation, origin checks, audit correlation, and stale-session handling.

## Role Model

The design roles are `viewer`, `operator`, `reviewer`, `admin`, `auditor`, and
`system_service`. Roles label what a local operator may see or request. Roles
do not bypass Brain policy. High-risk and write-like paths still require
policy, audit, approval, and autonomy gates where applicable.

## Permission Model

Permissions are action vocabularies mapped through policy. Read-only console
views are separate from governed dry-run action requests and review records.
No role can execute, activate, load code, register routes, enable providers,
store credentials, hard delete, or bypass policy in this phase.

## Static Console Implications

The static console remains local and unauthenticated. It may show role and
access-matrix examples, but it must not claim production login support. It must
not collect credentials, persist session material, or expose privileged
shortcuts.

## Operator Action Implications

Governed operator actions from AION-092 remain dry-run request, preview,
blocker, review, and query records only. Auth design may describe which roles
can request, preview, review, dismiss findings, and export redacted summaries.
It does not authorize execution.

## Audit Requirements

Future auth work must correlate actor id, workspace id, owner scope, role
labels, session id, policy decisions, audit ids, and provenance refs. Missing
audit correlation is a no-go condition for production authentication.

## Future Implementation Stages

- AION-094: Local auth contract and dev-only identity simulation.
- AION-095: Read-only local session prototype.
- AION-096: Role-aware console view filtering.
- AION-097: Dry-run action authorization enforcement.
- AION-098: Production auth architecture decision.
- AION-099: Production auth prototype behind disabled flag.

No production auth may be implemented before AION-098.

## Explicit Exclusions

- No production auth is implemented.
- No credentials are stored.
- No external identity provider is integrated.
- No login endpoint is added.
- No passkey or WebAuthn runtime is added.
- No real sessions are created.
- No password storage is added.
- No API auth router is added.
- No database migration is added.
- No frontend dependency is added.
- No policy, audit, approval, autonomy, or ActorContext bypass is allowed.

## AION-094 Contract Follow-Up

AION-094 implements a dev-only local auth contract and synthetic identity
simulation layer from this design. It adds local role permissions, local auth
contexts, role-aware console filtering, status, and audit checks.

It remains non-production: no login endpoint, no credential storage, no session
storage, no external identity provider integration, no write grant, no
execution grant, and no activation grant.
