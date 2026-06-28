# Operator Session Boundary

## Local Session Concept

A future local session is the boundary between a browser instance and a local
Operator Console instance. It is a design concept only in AION-093.

## Current AION-093 State

- Session is future design only.
- No cookies are implemented.
- No tokens are implemented.
- No browser session storage is introduced.
- Static console has no authenticated session.
- ActorContext remains the internal backend context mechanism.

## Future Session Lifecycle

A future implementation must define:

- session creation,
- session binding to actor id and workspace id,
- idle timeout,
- absolute timeout,
- secure logout,
- rotation,
- stale-session invalidation,
- audit correlation,
- local origin restrictions.

## Timeout Model

Timeouts must be explicit. A local session should expire after inactivity and
after a maximum absolute lifetime. Expired sessions must fail closed and must
not retain privileged state in the browser.

## Local Dev Mode Risk

Local dev mode is convenient but weak. It can be exposed accidentally through
shared machines, browser reuse, localhost trust assumptions, or stale pages.
Future session work must treat local access as untrusted until policy and audit
confirm the request.

## Audit Correlation

Future sessions must include correlation ids in audit records without storing
raw headers or credential material. Audit must show who acted, from which
workspace, under which scope, and through which policy decision.

## No-Go Conditions

- Session material stored insecurely.
- No timeout model.
- No logout model.
- No audit correlation.
- Browser state treated as authoritative.
- Policy bypass through a console session.

## AION-094 Session Boundary

AION-094 does not create sessions. `LocalAuthContext.session_present` must be
false, and the static console must not persist auth state in browser storage.
The simulation context is request data for local filtering only.

## AION-095 Local Session Prototype

AION-095 implements only the read-only local prototype side of this boundary.
The prototype makes future session semantics visible without production auth,
credential storage, token issuance, cookie issuance, browser sessions, or
database persistence.
