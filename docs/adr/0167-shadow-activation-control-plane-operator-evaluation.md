# ADR 0167: Shadow Activation Control-Plane Operator Evaluation

## Status

Accepted.

## Context

AION-180 authorized AION-181 to implement a disabled request, approval, monitoring, deactivation, and simulation control plane for future shadow activation. AION-181 delivered that implementation in PR #92 at feature commit `c7c7a5c83606399dff2221bd7f847ea00e177603` and merge commit `e9374853a53cd098096ed50da0fabb5874152d54`.

AION-182 verifies AION-181 delivery, evaluates the disabled control plane, and closes `AION-180-SI-0007`. It does not activate shadow mode and does not create an activation authorization or approval.

## Decision

AION-SACE-001 is adopted as the read-only operator evaluation record for the AION-181 disabled shadow activation control plane. The final decision is `SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW`.

AION-180-SI-0007 is consumed by AION-181. AION-180-SI-0007 is closed by AION-182. AION-SACE-001 is evidence and never approval. AION-SACE-001 is non-reusable. Synthetic approval evidence is simulation-only. AION-182 creates no implementation authorization, no activation approval, and no actual activation. Shadow activation remains disabled.

## Evaluation Coverage

The evaluation covers candidate binding, request and environment boundaries, synthetic approval evidence, separation of duties, local evidence adapter handling, output boundaries, resource budgets, state-machine transitions, monitoring, deactivation, kill-switch behavior, simulation, deterministic replay, concurrency, runtime-integration boundaries, repository integrity, and CI lineage.

The stale policy-check cancellation from PR #92 is historical. The policy-check rerun passed with no code change and is the authoritative final result.

## PASS Criteria

PASS requires every hard gate to pass, all 21 scenarios to execute and pass, repository integrity to remain unchanged, all side-effect counters to remain zero or false, and no v0.2 tag or release to exist.

## FAIL Criteria

Any failed approval, separation-of-duties, budget, protected-material, output-boundary, fingerprint, runtime influence, source mutation, Git mutation, PR creation, approval creation, active-state, production-environment, deployment, or repository-mutation hard gate produces FAIL.

## Consequences

A PASS recommends only an actual activation authorization review. A FAIL leaves the plane disabled and requires remediation authorization review. Future actual activation requires a separate explicit authorization bound to the exact AION-181 implementation commit and the AION-182 evaluation evidence.

No source rewrite, Git mutation, PR creation, approval creation, merge, promotion, canary, deployment, model training, v0.2 tag, or v0.2 release is authorized.

## Security, Privacy, and Operations

The evaluation uses synthetic and redacted evidence only. It stores no credentials, tokens, provider payloads, connector payloads, or unredacted personal data. Operationally, the control plane remains available only as disabled validation and simulation evidence until a separate authorization exists.
