# 0084: Local Auth Design For Operator Console

## Status

Accepted.

## Decision

AION creates a local auth design only for the Operator Console.

No auth runtime is added in AION-093. No external identity provider is
integrated. The static console remains unauthenticated and local-only.
ActorContext and policy remain authoritative for backend access.

## Reason

The Operator Console needs identity, role, session, and access-matrix design
before auth implementation. This keeps later local-login and production-auth
work bounded by policy, audit, approval, autonomy, and redaction gates.

## Consequence

Future auth work has clear boundaries, staged implementation, and no-go
conditions. AION-093 can be verified through docs, examples, and static checks
without adding runtime auth risk.

## Constraints

- No credentials.
- No sessions.
- No production auth claim.
- No external identity provider.
- No login endpoint.
- No privileged bypass.
- No policy bypass.
- No audit bypass.
