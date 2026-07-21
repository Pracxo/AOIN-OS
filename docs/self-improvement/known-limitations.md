# Known Limitations

The AION-175 platform is intentionally implemented but disabled.

## Current Limits

- Production runtime self-improvement is not enabled.
- AION-177 authorized AION-178 shadow-mode implementation only; AION-179 has
  closed that authorization, and shadow mode remains runtime-disabled.
- Production source rewrite is not enabled.
- Production canary exposure is not enabled.
- Model-backed patch generation is not enabled by default.
- GitHub operations remain adapter-driven and must be explicitly configured.
- Adaptive-learning outputs are data-only candidates and do not activate runtime behavior directly.
- Preference learning is user-scoped and reversible, but high-impact preference changes still require approval.
- Procedural skill evolution records data-only steps and cannot generate executable source.
- Model-weight training is not part of this platform.

## Required Future Work Before Activation

Any future activation requires a new authorization, exact approval record, full security review, rollback plan, production observability plan, protected-core review where applicable, holdout validation, full CI, and explicit operator acceptance.
## AION-180 Limitations

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.

The activation control plane is authorized but not implemented, and actual operator-invoked activation remains unavailable.

## AION-182 Shadow Activation Evaluation Closeout

AION-182 records `AION-SACE-001` with decision `SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW`. The AION-181 control plane is implemented, evaluated, and disabled. `AION-180-SI-0007` is closed, consumed by AION-181 PR #92, expired, and non-reusable.

No implementation authorization, activation approval, actual activation, source mutation, Git mutation, real control-plane PR, merge, promotion, canary, deployment, model training, provider call, connector call, network call, v0.2 tag, or v0.2 release is created by AION-182.
