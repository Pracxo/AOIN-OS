# Dry-Run Action Permission Model

AION-097 connects local auth roles to governed operator action authorization.

Role behavior:

- `operator` can request dry-run preview authorization.
- `reviewer` can request review record authorization.
- `viewer` cannot request dry-run operator action authorization.
- `auditor` cannot request dry-run operator action authorization.
- unknown roles fail closed.

The role matrix is advisory proof for local development only. It is not
production auth, does not store credentials, and does not create sessions.

Every authorization decision keeps:

- `write_allowed=false`
- `execution_allowed=false`
- `activation_allowed=false`
- `external_calls_allowed=false`

## AION-098 Future Production Auth Relationship

Future OIDC-compatible production auth may identify an operator only after a
later gated implementation. It must not bypass dry-run action authorization.
No production auth is implemented in AION-098, no provider integration is added
in AION-098, and `production_auth_enabled` remains false.
## AION-104 Prototype Review Gate

AION-104 keeps action authorization dry-run only. Authorization evidence may
allow request, preview, or review records, but it does not execute actions,
activate modules, write target systems, call external services, add auth
credentials, issue tokens or cookies, persist sessions, or bypass policy.
