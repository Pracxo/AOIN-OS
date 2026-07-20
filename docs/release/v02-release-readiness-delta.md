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

The current critical path has advanced through controlled shadow-mode
authorization, implementation, and AION-179 operator evaluation closeout.
`AION-177-SI-0006` is closed and non-reusable. The PASS recommendation does not
activate production self-improvement, production authentication, external
providers, production canary traffic, deployment, or model-weight training.

Completion of the self-improvement implementation program does not make v0.2
release-ready. Production runtime integration and release-candidate work remain
separate future authorization tracks.

## Historical Compatibility Markers

These markers preserve inherited v0.2 authorization-test references. They are
not the current critical path.

- AION-163-PA-0007
- The next critical path is AION-164.
## AION-178 Delta

AION-178 adds disabled, read-only self-improvement shadow-mode infrastructure.
It does not make v0.2 release-ready, does not create a v0.2 tag or release,
does not move `aion-v0.1.0`, and does not approve production runtime
activation.

## AION-179 Delta

AION-179 adds read-only shadow-mode operator evaluation closeout evidence and a
PASS recommendation for future controlled activation authorization review. It
does not make v0.2 release-ready, create a v0.2 tag or release, move
`aion-v0.1.0`, create a new implementation authorization, or approve production
runtime activation.
## AION-180 Delta

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.

This does not make v0.2 release-ready.
