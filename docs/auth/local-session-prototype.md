# Local Session Prototype

AION-095 introduces a local session prototype for Operator Console previews.
It is local-only, read-only, dev/test-only, and synthetic.

The prototype exposes:

- `POST /brain/local-session/preview`
- `POST /brain/local-session/context`
- `GET /brain/local-session/status`
- `POST /brain/local-session/boundary-check`
- `POST /brain/local-session/audit`

Local session previews may show actor id, workspace id, roles, owner scope,
expiry metadata, and role-aware filtering context. They do not authenticate
users, store credentials, issue tokens or cookies, create browser sessions, or
persist production session state.

Privileged flags are hard false: `write_allowed=false`,
`execute_allowed=false`, `activation_allowed=false`, and
`external_calls_allowed=false`.

## AION-096 Role Filtering

Local session context can be used as input to role-aware console filtering.
The session context remains read-only and cannot expand the permissions that
the local role matrix denies.

## AION-097 Action Authorization Boundary

Dry-run action authorization can consume local session context metadata. A
denied, invalid, non-read-only, write-capable, execution-capable,
activation-capable, or external-call-capable session context blocks the
authorization decision.
## AION-104 Prototype Review Gate

AION-104 keeps local sessions as read-only previews. The review gate records
that local session context remains synthetic and cannot persist browser state,
issue tokens or cookies, store credentials, authenticate users, grant writes,
grant activation, grant execution, or call external identity providers.
