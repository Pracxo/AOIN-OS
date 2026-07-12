# Production Auth Prerequisites

Production authentication is not implemented in AION-093. Before production
auth can exist, AION requires:

- production identity provider design,
- credential storage design,
- session storage design,
- CSRF protection,
- CORS and origin policy,
- audit correlation,
- role provisioning,
- break-glass design,
- secure logout,
- token rotation,
- secrets handling,
- security review,
- release gate.

## Identity Provider Design

The identity provider architecture must define account source, lifecycle,
roles, groups, trust boundaries, fallback behavior, and failure modes before
integration work begins.

## Credential And Session Storage

Credential and session storage must be designed before implementation. AION
must not store credentials or session material until storage, encryption,
rotation, logout, and audit semantics are reviewed.

## Browser And API Protection

Future production auth must define CSRF protection, CORS rules, origin checks,
clickjacking controls, and localhost trust boundaries. Browser state must not
be treated as authoritative.

## Audit And Release Gate

Auth events must correlate with ActorContext, policy decisions, audit records,
and provenance refs. Production auth requires security review and release gate
approval.

## AION-098 Architecture Decision

AION-098 recommends OIDC-compatible production auth as the future primary path
and reverse proxy auth as an optional deployment pattern. This is design only.
No production auth is implemented in AION-098. No provider integration is added
in AION-098. No credentials, tokens, sessions, or cookies are created, stored,
issued, or accepted. `production_auth_enabled` remains false.

## AION-151 Scoped Production Auth Authorization

AION-151 adds the canonical scoped authorization transaction `AION-151-PA-0001` for `production-auth-core` and future task `AION-152`. The authorization is limited to the `disabled-production-auth-core` implementation scope. Production-auth runtime remains disabled, runtime guard releases remain false, endpoint/storage/provider/external-call approvals remain false, package and migration changes remain false, and no v0.2 tag or release is created.
