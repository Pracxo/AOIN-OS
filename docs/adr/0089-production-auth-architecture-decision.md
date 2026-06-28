# 0089: Production Auth Architecture Decision

## Status

Accepted for future architecture. No runtime implementation.

## Context

AION-093 through AION-097 established local auth design, dev-only identity
simulation, read-only local session previews, role-aware console filtering, and
dry-run action authorization. Production auth still needs an approved
architecture before any runtime identity provider integration exists.

## Decision

- Decision: choose OIDC-compatible production auth architecture as future
  primary path.
- Decision: reverse proxy auth may be supported as deployment pattern later.
- Decision: no production auth runtime is implemented in AION-098.
- Decision: no secrets, tokens, sessions, cookies, or provider calls are added.
- Decision: AION-099 may add disabled prototype only.

## Reason

AION needs production auth architecture before runtime auth. The Operator
Console and Brain API must preserve ActorContext, policy, audit, role matrix,
and dry-run action authorization boundaries while planning real identity
integration.

## Consequence

Later implementation must satisfy release gates and threat model. Runtime auth
work must prove provider validation, token/session handling, CSRF/CORS posture,
role mapping, revocation, audit correlation, security review, and rollback
before enablement.

## Constraints

- Constraint: `production_auth_enabled` remains false.
- Constraint: no external identity integration.
- Constraint: no credentials.
- Constraint: no privileged bypass.
- Constraint: no login/logout endpoints.
- Constraint: no package dependencies or provider SDKs.
- Constraint: no migrations or session storage.
