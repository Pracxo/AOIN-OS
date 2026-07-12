# v0.2 Production Auth Implementation Scope

## Permitted for AION-152

- internal production-auth contracts
- internal production-auth configuration model
- disabled-by-default feature flags
- policy interfaces
- audit events
- provenance events
- redacted diagnostics
- deterministic test fixtures
- unit and integration tests
- documentation
- read-only static-console evidence

## Prohibited for AION-152

- runtime enablement
- login endpoints
- logout endpoints
- authentication callback endpoints
- credential storage
- password storage
- token issuance
- token storage
- sessions
- cookies
- provider calls
- provider SDKs
- migrations
- package dependencies
- frontend dependencies
- external calls
- operator writes
- connector runtime
- module activation
- sandbox execution
- release or tag creation

## Boundary

The only approved candidate is `production-auth-core`. The only approved
workstream is `production-auth-implementation`. The only approved
authorization scope is `disabled-production-auth-core`.
