# Connector Simulator No-Go Conditions

AION-110 must remain a local synthetic simulator only.

Forbidden in this milestone:

- enabling connector runtime
- adding connector SDKs or provider SDKs
- adding network clients for connector execution
- resolving DNS for connector work
- storing credentials or tokens
- adding OAuth, OIDC, or SAML runtime
- enabling production auth
- enabling external model calls or notifications
- enabling module or capability activation
- loading code
- registering runtime routes
- executing tools, action proposals, or write paths
- hard-deleting records
- adding frontend dependencies, package files, lockfiles, migrations, or domain
  module logic

Use:

```bash
./scripts/connector-simulator-no-go-regression.sh
```

The regression check is intentionally narrow: it allows synthetic simulator
docs, fixtures, static demo data, SDK/CLI wrappers, and API route wiring while
failing runtime activation, external egress, credential material, token
material, route registration, and dependency drift.
