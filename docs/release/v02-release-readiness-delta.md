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

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

Historical AION-181 note: at implementation time, AION-180-SI-0007 remained active pending the later AION-182 closeout. AION-182 subsequently closed that authorization as consumed, expired, and non-reusable; actual activation still requires a separate future authorization.

## AION-182 Shadow Activation Evaluation Closeout

AION-182 records `AION-SACE-001` with decision `SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW`. The AION-181 control plane is implemented, evaluated, and disabled. `AION-180-SI-0007` is closed, consumed by AION-181 PR #92, expired, and non-reusable.

No implementation authorization, activation approval, actual activation, source mutation, Git mutation, real control-plane PR, merge, promotion, canary, deployment, model training, provider call, connector call, network call, v0.2 tag, or v0.2 release is created by AION-182.

## AION-203 Cognitive Architecture Program Closeout

AION-203 records `AION-CASE-001` with decision `CONTROLLED_LOCAL_OFFLINE_PILOT_PASS_COMPLETE_COGNITIVE_ARCHITECTURE_PROGRAM`. The AION Cognitive Architecture Program is complete: persistent cognitive state, predictive world model, global cognitive workspace, memory consolidation, hierarchical counterfactual planning, active information acquisition, governed continual learning, integrated cognitive shadow runtime, and the controlled local-offline cognitive pilot are available as governed evidence. Production cognitive runtime, production event subscription, unrestricted network access, source rewriting, automatic merge, production canary, production deployment, and model-weight training remain disabled.

## AION-204 Knowledge Intelligence Program Authorization

AION-204 creates `AION-KNOWLEDGE-INTELLIGENCE-001` and `AION-204-KI-0001` as the sole active Knowledge Intelligence implementation authorization for AION-205. The authorized scope is `disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core`. Research plane authorized=true, research plane implemented=false, research runtime enabled=false, network access enabled=false, background crawler enabled=false, automatic knowledge promotion enabled=false, cognitive belief mutation enabled=false, source mutation enabled=false, Git mutation enabled=false, production exposure=false, and model-weight training enabled=false. AION-206 is the formal closeout task.

## AION-205 Controlled Research Acquisition Core

AION-205 implements the controlled research acquisition and immutable source-snapshot core as operator-invoked and runtime-disabled. Acquired content remains untrusted evidence; factual claim verification, knowledge promotion, cognitive belief mutation, public network fetch, crawler execution, search-provider integration, connector integration, source mutation, Git mutation, automatic merge, deployment, and model-weight training remain disabled. AION-204-KI-0001 is closed by AION-206; AION-206-KI-0002 is active for AION-207 source registry authorization.


## AION-206 source registry authorization

AION-206 records `RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION`, closes `AION-204-KI-0001`, and creates `AION-206-KI-0002` for AION-207 only. The source registry core is implemented as immutable in-memory metadata only; runtime, persistent registry writes, network, source body persistence, claim verification, knowledge promotion, and belief mutation remain disabled pending AION-208 formal closeout.


## AION-206 Source Registry Authorization

AION-206 records `RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION`, closes `AION-204-KI-0001`, and creates `AION-206-KI-0002` for AION-207 only. The source registry core is implemented as immutable in-memory metadata only; research runtime, source registry runtime, persistent registry writes, network access, source body persistence, claim verification, knowledge promotion, belief mutation, source mutation, Git mutation, PR creation, approvals, merges, deployments, model-provider calls, v0.2 tags, and v0.2 releases remain disabled pending AION-208 formal closeout.


## AION-208 Knowledge Intelligence State

AION-208 completed read-only operator evaluation `AION-SPRE-001` for the AION-207 append-only source provenance registry. The registry remains metadata-only, in-memory, and persistent-write-disabled. `AION-206-KI-0002` is closed and non-reusable. `AION-208-KI-0003` is the sole active Knowledge Intelligence implementation authorization for AION-209. AION-209 may implement the temporal claim-evidence graph, but automatic claim extraction, truth decisions, confidence calculation, knowledge promotion, cognitive belief mutation, persistent graph writes, source-body storage, network access, source mutation, Git mutation, runtime PRs, automatic merge, deployment, and model training remain disabled.

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.
