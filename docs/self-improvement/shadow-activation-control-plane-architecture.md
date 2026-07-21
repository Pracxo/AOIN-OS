# Shadow Activation Control Plane Architecture

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.


## Authorized Control Plane

AION-181 may define contracts, validators, a disabled state machine, simulation-only decisions, monitoring contracts, deactivation contracts, diagnostics, audit provenance, and operator review evidence. It may not activate AION-178 or register with kernel, startup, scheduler, background, production-event, network, connector, provider, Git, PR, merge, deployment, canary, or model-training surfaces.

## Future Source Scope

May create:

- services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py
- services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py

May update:

- services/brain-api/src/aion_brain/self_improvement/__init__.py

Must not modify:

- services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py
- services/brain-api/src/aion_brain/self_improvement/shadow_mode.py
- services/brain-api/src/aion_brain/self_improvement/shadow_observation.py
- services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py
- services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py
- services/brain-api/src/aion_brain/self_improvement/shadow_budget.py
- services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py
- services/brain-api/src/aion_brain/self_improvement/shadow_runner.py
- services/brain-api/src/aion_brain/self_improvement/governance.py
- services/brain-api/src/aion_brain/self_improvement/approval.py
- services/brain-api/src/aion_brain/self_improvement/protected_paths.py
- services/brain-api/src/aion_brain/self_improvement/risk.py
- services/brain-api/src/aion_brain/self_improvement/worktree.py
- services/brain-api/src/aion_brain/self_improvement/patch_generator.py
- services/brain-api/src/aion_brain/self_improvement/git_controller.py
- services/brain-api/src/aion_brain/self_improvement/pr_controller.py
- services/brain-api/src/aion_brain/self_improvement/merge_controller.py
- services/brain-api/src/aion_brain/self_improvement/canary.py
- services/brain-api/src/aion_brain/self_improvement/rollback_controller.py
- services/brain-api/src/aion_brain/policy/
- services/brain-api/src/aion_brain/audit/
- services/brain-api/src/aion_brain/security/
- services/brain-api/src/aion_brain/kernel/
- services/brain-api/src/aion_brain/api/
- services/brain-api/src/aion_brain/api_support/
- services/brain-api/src/aion_brain/config.py
- services/brain-api/pyproject.toml
- packages/aion-sdk-python/src/
- migrations/
- .github/workflows/

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

AION-180-SI-0007 remains active pending AION-182 closeout. AION-182 is the next formal closeout and operator-evaluation task. Actual activation requires another authorization after AION-182.

## AION-182 Shadow Activation Evaluation Closeout

AION-182 records `AION-SACE-001` with decision `SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW`. The AION-181 control plane is implemented, evaluated, and disabled. `AION-180-SI-0007` is closed, consumed by AION-181 PR #92, expired, and non-reusable.

No implementation authorization, activation approval, actual activation, source mutation, Git mutation, real control-plane PR, merge, promotion, canary, deployment, model training, provider call, connector call, network call, v0.2 tag, or v0.2 release is created by AION-182.
