# Local Auth Contract

AION-094 adds a local-only auth contract for Operator Console development.

This is not production authentication. No login endpoint is added. No credentials are stored. No sessions are created. No external identity provider is integrated.

The contract defines synthetic local operator identities, local roles, local auth contexts, role permissions, console filtering requests, and local auth audit results. Every generated auth context keeps `production_auth=false`, `credentials_present=false`, `session_present=false`, `write_allowed=false`, `execute_allowed=false`, `activation_allowed=false`, and `external_calls_allowed=false`.

The API surface is limited to:

- `GET /brain/local-auth/roles`
- `POST /brain/local-auth/simulate`
- `POST /brain/local-auth/filter-console`
- `POST /brain/local-auth/audit`
- `GET /brain/local-auth/status`

These endpoints shape local development view filtering only. They do not authenticate real users, issue tokens, set cookies, persist sessions, bypass policy, grant execution, or activate modules.

## AION-095 Local Session Relationship

AION-095 builds on local auth by deriving read-only session context from
synthetic local identity. The session preview is not a credential, not a token,
not a cookie, not production auth, and not persisted state. Local auth remains
the role source for console filtering, while local session contracts keep write,
execution, activation, and external calls disabled.

## AION-096 Role Access Contracts

Local auth now includes role access decisions and role access audits. These
contracts prove view, section, and descriptor visibility without granting
write, execution, activation, external-call, production-auth, or credential
capability.

## AION-097 Action Authorization Link

Dry-run action authorization consumes local auth roles as input. It accepts the
role context only for dry-run previews and review records, and it still keeps
write, execution, activation, external-call, production-auth, and credential
capabilities disabled.
