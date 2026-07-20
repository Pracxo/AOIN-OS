# Runtime Activation Checklist

AION-175 does not activate runtime self-improvement. This checklist defines the minimum evidence required before any future activation request can be reviewed.

AION-177 also does not activate runtime self-improvement. It authorized the
AION-178 shadow-mode implementation only. AION-178 sets
`shadow_mode_implemented=true` with
`shadow_mode_implementation_state=implemented_operator_invoked_disabled`; any
runtime activation still requires a later explicit authorization.

AION-179 closes `AION-177-SI-0006` after a PASS operator evaluation. That PASS is
not activation approval and does not create a new implementation authorization.

## Required Evidence

- New authorization transaction with exact implementation scope.
- Exact human approval for commit, diff hash, benchmark fingerprint, rollback commit, deployment artifact, exposure budget, monitoring duration, and metric thresholds.
- Full security review and protected-core impact review.
- Holdout benchmark validation with unchanged holdout content.
- Test-integrity report proving no test weakening.
- Production observability plan.
- Rollback plan with verified rollback commit.
- Canary exposure budget with production exposure disabled until separately approved.
- Full CI success on the exact approved commit.

## Current Required Values

- `self_improvement_runtime_enabled=false`
- `self_rewrite_runtime_enabled=false`
- `automatic_merge_enabled=false`
- `production_canary_enabled=false`
- `production_deployment_enabled=false`
- `model_weight_training_enabled=false`
## AION-180 Update

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.

Required future actual activation evidence must bind exact AION-181 implementation commit, tree, diff, benchmark, rollback, operator, reference-set, run-budget, monitoring, retention, and deactivation evidence.

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

AION-180-SI-0007 remains active pending AION-182 closeout. AION-182 is the next formal closeout and operator-evaluation task. Actual activation requires another authorization after AION-182.
