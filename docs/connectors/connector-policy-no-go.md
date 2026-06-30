# Connector Policy No-Go Conditions

The connector policy catalog cannot introduce any runtime connector behavior.

No-go conditions:

- no connector runtime enablement
- no external calls
- no connector or provider SDK dependency
- no network client
- no credential storage
- no token storage
- no production auth
- no external identity provider runtime
- no route registration
- no module activation
- no capability activation
- no code loading
- no tool execution
- no write execution
- no hard delete
- no frontend dependency
- no package files
- no migrations

The local regression script `./scripts/connector-policy-no-go-regression.sh`
checks these boundaries for the AION-111 artifacts. If a future task needs any
runtime path, it must be a separate milestone with a new ADR, threat model,
operator review, and release gate.
