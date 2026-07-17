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

## Remaining Blockers

- Real identity verification
- External provider integration
- Protected-material handling decision
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

AION-160 remediates the actor-context trust boundary under `AION-159-PA-0005`.
The implementation removes non-development trust in identity-bearing `X-AION`
headers, preserves explicit development simulation behind the exact development
gate, uses RequestIdentityContext as primary identity evidence, projects safe
trace and correlation from RequestContext, and returns anonymous
zero-permission ActorContext outside development simulation.

The implementation remains observe-only and disabled unless a future
authorization explicitly changes the runtime guard state.
