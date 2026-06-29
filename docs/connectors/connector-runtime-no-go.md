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
