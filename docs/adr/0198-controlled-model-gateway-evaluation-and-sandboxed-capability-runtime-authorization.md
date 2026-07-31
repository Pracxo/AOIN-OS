# ADR 0198: Controlled Model-Gateway Evaluation and Sandboxed Capability-Runtime Authorization

## Status

Accepted by AION-234.

## Context

AION-233 implemented a provider-neutral model gateway that can validate bounded requests, closed provider and model manifests, deterministic routing, fallback and retry plans, circuit-breaker state, structured outputs, response safety, provenance, audit, health, and integrity through a deterministic reference provider. It cannot execute a capability, call an external connector, or execute a tool.

## Decision

AION-234 records `AION-SRIPE-002` as `CONTROLLED_PROVIDER_NEUTRAL_MODEL_GATEWAY_OPERATOR_EVALUATION_PASS_RECOMMEND_SANDBOXED_CAPABILITY_RUNTIME_AUTHORIZATION`. `AION-232-SRI-0002` is closed as consumed by AION-233. `AION-234-SRI-0003` is created as the sole active Secure Runtime Integration authorization for AION-235.

AION-235 is authorized to implement only a sandboxed deterministic capability runtime for closed, schema-validated, in-memory reference operations and synthetic reference connectors. Model output remains an untrusted proposal and cannot trigger execution without explicit operator capability selection.

## Consequences

AION-236 becomes the formal evaluation and operator-console integration authorization decision after AION-235. AION-237 remains unauthorized. AION-238 remains the final Secure Runtime Integration Program evaluation and v0.2 release-candidate review. External connectors, real tools, network, credentials, filesystems, processes, shell, subprocess, browser, dynamic import, eval, exec, packages, modules, production memory, production policy, beliefs, source rewrite, deployment, model training, v0.2 tags, and v0.2 releases remain disabled.
