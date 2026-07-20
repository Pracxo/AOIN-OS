# Shadow Activation Deactivation

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.


Automatic deactivation triggers:

- any network call
- any connector call
- any provider call
- any Git operation
- any source mutation
- any PR creation
- any approval creation
- any runtime promotion
- any runtime influence
- any output-boundary escape
- any redaction failure
- any holdout disclosure
- any protected-material exposure
- any fingerprint mismatch
- any budget violation
- any unknown reference type
- any stale or expired approval
- activation window expiry
- run-count exhaustion
- operator kill switch

Deactivation must stop future runs, preserve immutable evidence, create a redacted incident record, avoid source or runtime rollback action, and require a new authorization before reactivation.

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

AION-180-SI-0007 remains active pending AION-182 closeout. AION-182 is the next formal closeout and operator-evaluation task. Actual activation requires another authorization after AION-182.
