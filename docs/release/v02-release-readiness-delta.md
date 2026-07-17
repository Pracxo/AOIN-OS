# v0.2 Release Readiness Delta

Status: `not-ready`

## Current Strengths

- Brain kernel
- Contract model
- Policy and audit model
- Governance and scoped authorization
- CI and regression infrastructure
- Internal production-auth core
- Production-auth stabilization
- Disabled request identity boundary
- Request identity implementation evidence
- Request identity stabilization
- Actor-context trust-boundary remediation
- Fail-closed ActorContext resolution
- Non-development identity-header rejection
- Anonymous zero-permission fallback
- Development identity simulation isolation

## Remaining Blockers

- Offline cryptographic identity verification core and later request integration
- request-level verified identity integration
- replay protection
- External provider integration
- Protected-material handling decision beyond public verification keys
- Credential lifecycle
- Token lifecycle
- Session lifecycle
- Deployment artifact
- Rollback procedure
- Operational observability
- Threat-model review
- Release-candidate validation
- Runtime guard release decision
- v0.2 tag and release approval

## v0.2 Release Exit Criteria

1. One controlled end-to-end request identity path.
2. Provider-agnostic verification interface.
3. No secret persistence without separate approval.
4. Audit and provenance coverage.
5. Runtime guard release decision.
6. Deployment and rollback evidence.
7. Full CI and security checks.
8. Release candidate review.
9. Explicit v0.2 tag and release authorization.

## Release State

- `v02_release_ready=false`
- `v02_tag_created=false`
- `v02_release_created=false`

## Next Critical Path

`AION-162` is the next critical path.

AION-162 implements the offline Ed25519 identity assertion verification core
authorized by `AION-161-PA-0006`.

The next core may verify signatures and claims offline with public keys, but it
must not authenticate requests, apply ActorContext, apply RequestIdentityContext,
parse HTTP headers, contact providers, create a replay cache, or release runtime
guards. Later request integration remains a separate blocker.
