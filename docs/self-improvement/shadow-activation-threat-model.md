# Shadow Activation Threat Model

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.


Core rule: `AION-180-SI-0007` authorizes construction of a disabled activation control plane. It does not authorize activation.

Threats addressed:

- evaluation PASS mistaken for activation approval
- AION-177-SI-0006 reuse
- AION-180-SI-0007 mistaken for runtime activation authority
- forged activation candidate
- changed candidate commit after approval
- changed diff after approval
- changed benchmark evidence after approval
- changed reference set after approval
- changed output boundary after approval
- changed run budget after approval
- changed monitoring thresholds after approval
- changed deactivation plan after approval
- stale approval
- replayed approval
- self-approval
- duplicate approvers
- operator identity spoofing
- security reviewer spoofing
- reference bundle substitution
- local file path traversal
- symlink escape
- hidden file input
- oversized evidence bundle
- unredacted request-material smuggling
- private reasoning-material smuggling
- credential or token smuggling
- personal-data leakage
- source-patch smuggling
- raw-diff smuggling
- output directory escape
- reference flooding
- proposal flooding
- budget bypass
- runtime influence
- active-learning promotion
- network fallback
- background activation
- production event subscription
- activation outside the approved time window
- run-count overrun
- deactivation suppression
- evidence deletion
- activation evidence mistaken for implementation approval
- production activation without another authorization

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

AION-180-SI-0007 remains active pending AION-182 closeout. AION-182 is the next formal closeout and operator-evaluation task. Actual activation requires another authorization after AION-182.
