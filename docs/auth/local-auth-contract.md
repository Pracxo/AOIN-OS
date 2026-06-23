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
