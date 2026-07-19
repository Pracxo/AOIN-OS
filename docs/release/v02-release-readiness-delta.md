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
- Offline Ed25519 verification
- Public-key registry
- Deterministic cryptographic regression coverage
- Persistent replay protection
- Governed self-improvement control plane
- Immutable benchmark plane
- Approval-bound rewrite control
- Canary and rollback simulation
- Adaptive-learning candidates

## Remaining Blockers

- Operator evaluation
- Production-auth runtime integration
- Production replay-ledger schema provisioning
- Request-level verified identity integration
- Identity-provider integration
- Operational public-key provisioning and rotation evidence
- Protected-material lifecycle
- Credential lifecycle
- Token lifecycle
- Session lifecycle
- Production deployment artifact
- Rollback operations
- Production observability
- Threat-model review
- Runtime guard release decision
- Release-candidate validation
- v0.2 tag and release authorization

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

## Current Critical Path

The current critical path has advanced past operator evaluation into controlled
shadow-mode authorization. AION-177 creates `AION-177-SI-0006` for future
AION-178 disabled, observation-only shadow-mode implementation. This
authorization does not activate production self-improvement, production
authentication, external providers, production canary traffic, deployment, or
model-weight training.

Completion of the self-improvement implementation program does not make v0.2
release-ready. Production runtime integration and release-candidate work remain
separate future authorization tracks.

## Historical Compatibility Markers

These markers preserve inherited v0.2 authorization-test references. They are
not the current critical path.

- AION-163-PA-0007
- The next critical path is AION-164.
