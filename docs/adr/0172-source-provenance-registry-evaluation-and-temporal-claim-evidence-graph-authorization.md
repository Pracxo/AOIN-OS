
# ADR 0172: Source Provenance Registry Evaluation and Temporal Claim-Evidence Graph Authorization

## Context

AION-206 authorized AION-207 to implement an append-only metadata-only source provenance registry. AION-207 was delivered through PR #119, feature commit `3e95d788726be4d3f51f299aa005df87aa00375b`, and merge commit `14c12bebfced7fd6345c8af2899988aadfa91a44`. Final CI passed before AION-208 closeout.

## Decision

AION-208 runs `AION-SPRE-001`, a read-only source provenance registry operator evaluation with exactly 28 scenarios. The exact decision is `SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION`.

## Evaluation Method

The harness uses public AION-207 APIs only. It evaluates record envelopes, source-body exclusion, budgets, persistent-write rejection, append-only semantics, idempotency, sequence and fingerprint integrity, supersession, fixtures, indexes and queries, integrity auditing, evidence redaction, deterministic replay, concurrency isolation, and repository-integrity totals. Corrective PRs are recorded when present; none were required.

## Findings

Record envelopes were immutable and fingerprinted. Source bodies and previews remained absent. Registry record, envelope, metadata, lineage, and citation budgets were enforced. Persistent writes failed closed with write batch zero. Append-only sequence, idempotency, versioning, fixture replay, exact queries, integrity checks, evidence redaction, deterministic replay, and concurrency isolation passed. The registry created no source mutation, Git mutation, PR, approval, merge, deployment, network request, DNS request, truth decision, confidence calculation, knowledge promotion, belief mutation, persistent write, v0.2 tag, or v0.2 release.

## Closeout

`AION-206-KI-0002` is consumed by AION-207, closed by AION-208, inactive, expired, and non-reusable. On PASS, AION-208 creates `AION-208-KI-0003` as the sole active Knowledge Intelligence authorization for AION-209.

## Temporal Graph Boundary

AION-209 may implement an immutable temporal claim-evidence graph for explicit unverified claims, evidence links, time, jurisdiction, versions, corrections, retractions, and structural contradiction candidates. It must not extract claims automatically, determine truth, calculate epistemic confidence, promote knowledge, mutate cognitive beliefs, write persistent graph state, store source bodies, or acquire network content.

## Security Impact

Persistent registry and graph writes remain disabled. Source bodies remain absent. Network access, source mutation, Git mutation, runtime PRs, approvals, automatic merge, deployment, and model-weight training remain disabled.

## Privacy Impact

Evaluation evidence is synthetic and redacted. The graph authorization forbids raw source content, raw prompt storage, hidden reasoning storage, credentials, cookies, authorization headers, and unredacted personal data.

## Operational Impact

AION-209 becomes the next task. AION-210 will evaluate AION-209 before any future truth-engine authorization. AION-211 remains the future epistemic truth engine.

## Consequences

The source registry is now evaluated and closed out. Temporal claim graph implementation is authorized but absent. All runtime and persistence boundaries remain fail-closed.
