# Connector Runtime No-Go Conditions

AION-108 remains blocked if any of these are introduced:

- connector runtime enabled
- external URL calls
- DNS resolution for connectors
- `requests`, `httpx`, `aiohttp`, or `urllib` connector call paths
- connector SDK dependency
- provider SDK dependency
- credential storage
- token storage
- OAuth, OIDC, or SAML runtime
- dynamic route registration
- connector activation
- capability activation
- module activation
- code loading
- tool execution
- action proposal execution
- policy bypass
- audit bypass

These no-go conditions are enforced by local tests and
`scripts/connector-runtime-check.sh`.

## AION-109 Review Gate Relationship

AION-109 extends the no-go posture with
`scripts/connector-runtime-no-external-call-regression.sh`. The new regression
keeps runtime source, API routers, SDK/CLI source, migrations, package files,
external call paths, credentials, tokens, dynamic routes, activation, policy
bypass, and audit bypass blocked for the review task.
