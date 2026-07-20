# ADR 0165: Controlled Shadow Activation Control-Plane Authorization

## Status

Accepted

## Context

AION-178 implemented disabled operator-invoked shadow observation. AION-179 evaluated it with AION-SOE-001 and returned `SHADOW_MODE_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ACTIVATION_AUTHORIZATION_REVIEW`. That result is supporting evidence only. It is not an approval, not an implementation authorization, not reusable, and cannot authorize activation.

## Decision

Create `AION-180-SI-0007` as the sole active implementation authorization for AION-181. Authorize AION-181 only to implement disabled activation-control contracts and validators, exact approval binding, reference-set binding, operator principal binding, output-boundary binding, run-budget binding, monitoring-plan binding, deactivation-plan binding, expiry and non-reuse enforcement, a disabled state machine, local evidence adapter boundaries, resource limits, diagnostics, audit provenance, kill switch contracts, incident records, operator review items, and simulation-only activation decisions.

Permit no active state, no runtime activation, no production data, no background execution, no network, no source or Git mutation, no PR or approval creation, no merge, no promotion, no canary or deployment, no model training, and no v0.2 tag or release.

## Security Impact

Exact future approval binding is mandatory across commit, tree, diff, evidence fingerprints, benchmark evidence, reference set, operator, security reviewers, output boundary, run budget, monitoring, deactivation, rollback, expiry, and non-reuse.

## Privacy Impact

Future AION-181 local evidence adapters must accept only explicit redacted local evidence bundles outside the repository and reject protected text, credentials, tokens, cookies, private keys, personal data, source patches, and raw diffs.

## Operational Impact

AION-182 must evaluate AION-181 and close `AION-180-SI-0007`. Future actual activation requires another authorization bound to exact AION-181 implementation evidence, rollback evidence, benchmarks, references, budget, monitoring, retention, and deactivation evidence.

## Consequences

Shadow mode runtime remains disabled. AION-180 authorizes construction of a disabled activation control plane. It does not authorize activation.
