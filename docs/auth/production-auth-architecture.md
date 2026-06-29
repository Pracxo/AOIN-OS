# Production Auth Architecture

## Purpose

AION-098 decides the future production auth architecture before any runtime auth
is built. This is design only. No production auth is implemented in AION-098.
No provider integration is added in AION-098. No credentials, tokens, sessions,
or cookies are created, stored, issued, or accepted.

AION-099 adds a disabled production auth prototype for status, mock claims
preview, and audit only. It does not enable runtime auth or change the AION-098
architecture decision.
`production_auth_enabled` remains false.

## Current Local Auth State

AION-093 defined local auth design. AION-094 added dev-only local auth contracts
and synthetic identity simulation. AION-095 added read-only local session
previews. AION-096 added role-aware console filtering. AION-097 added dry-run
action authorization enforcement.

Those layers are local development and operator-safety proof only. They do not
authenticate real users and they do not replace policy, audit, ActorContext,
role matrix checks, or action authorization.

## Why Production Auth Is Not Implemented Yet

Production auth changes the trust boundary of the Operator Console and Brain
API. AION needs an approved provider model, token boundary, session boundary,
CSRF/CORS posture, audit correlation, role mapping, revocation behavior, and
release gates before runtime auth exists.

## Recommended Architecture

The recommended future architecture is OIDC-compatible production auth as the
primary path. AION should accept verified identity assertions only after a
dedicated auth boundary validates issuer, audience, expiry, nonce/state,
signature, revocation posture, and role/group mapping.

Reverse proxy auth may be supported later as an optional deployment pattern
when the proxy is explicitly trusted and AION still verifies signed internal
identity assertions or equivalent boundary evidence.

## Rejected Alternatives

- SAML-only primary path: viable for some enterprises, but less ergonomic for
  Operator Console API flows than OIDC-compatible identity.
- Reverse proxy only: useful deployment pattern, but not sufficient as the sole
  architecture because spoofing and header trust require strict controls.
- Local enterprise SSO bridge as primary: too deployment-specific for the first
  production architecture.
- Passkey/WebAuthn first: promising future option, but not the first production
  integration path.
- Dev-only local auth as production auth: rejected. It is simulation only.

## Identity Flow

1. Operator authenticates with a trusted identity provider outside AION.
2. Future auth boundary validates the returned identity assertion.
3. AION maps stable subject, groups, and claims into ActorContext-compatible
   identity records.
4. Policy receives the mapped actor, workspace, roles, scope, and request
   context.
5. Audit records correlate provider subject reference, ActorContext, policy
   decision, request trace, and action authorization decision.

## Role Mapping

Provider groups and claims must map into AION roles through an explicit mapping
table or configuration approved by release gate. Unknown roles fail closed.
Stale mappings must be detectable, auditable, and revocable.

## Session Boundary

Future sessions must be short-lived, revocable, scoped, and auditable. Browser
state must not be treated as authoritative. AION-098 creates no session table,
no session persistence, no session cookie, and no login/logout endpoint.

## Token Boundary

Future tokens must stay inside the auth boundary. Public Brain contracts must
not expose token values. Logs, telemetry, examples, and docs must never include
real token material. AION-098 adds no token parser, token issuer, token store,
or provider SDK.

## Audit Boundary

Every future production auth event must correlate to trace id, ActorContext,
workspace, provider subject reference, mapped roles, policy decision, and
operator action authorization when present. Audit must record decisions and
metadata only, never credentials or token values.

## Policy Integration

Production identity may establish who the actor is. It must not self-authorize
Brain actions. Policy remains authoritative. Role mapping, action
authorization, approval, audit, and no-go checks remain required.

## Operator Console Integration

The Operator Console may later display auth status, mapped role, workspace
scope, and release-gate posture. It must not display credentials, token values,
cookie values, provider payloads, raw headers, raw prompts, or hidden
reasoning. It must not add a login UI until a future gated implementation task.

## Deployment Prerequisites

- provider selected and documented
- threat model approved
- token/session storage design approved
- CSRF and CORS design approved
- role/group mapping approved
- revocation and timeout behavior approved
- audit correlation tested
- disabled prototype green
- security review complete
- rollback plan approved

## Release Gates

Production auth runtime cannot ship until
`docs/auth/production-auth-release-gates.md` is satisfied. AION-099 may add a
disabled prototype behind flags only. That prototype must be mock-only, use
synthetic claims, make no external call, issue no real token, and remain off by
default.

## No-Go Conditions

- provider SDK added before release gate
- login/logout route added before release gate
- credential, token, cookie, or session value stored
- browser localStorage used for auth material
- policy bypass
- ActorContext bypass
- audit mismatch
- unreviewed role mapping
- reverse proxy header spoofing risk unresolved
- `production_auth_enabled` set true before approval
## AION-104 Prototype Review Gate

AION-104 does not implement the production auth architecture. It adds the
pre-implementation evidence gate that future auth tasks must satisfy before
changing runtime boundaries. Production auth remains disabled, and no provider
SDK, provider route, login/logout flow, credential store, token issuance, cookie
issuance, session persistence, migration, package file, or API router is added.
