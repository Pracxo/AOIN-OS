# Model Gateway Implementation

AION-233 implements the `AION-232-SRI-0002` controlled provider-neutral model
gateway. It composes the AION-231 authenticated local secure-runtime foundation
through `brain.think.simulate`, requires parent guard outcome
`allow_simulation`, and accepts only parent dispatch status `simulated`.

Implemented surfaces:

- Authorization envelope and secure-runtime component binding.
- Immutable provider and model manifests.
- Closed provider and model allowlists.
- Capability profiles.
- Local gateway session planning.
- Message and context normalization.
- System-instruction policy binding.
- Context and token budgets.
- Deterministic request fingerprints and replay idempotency.
- Deterministic routing, fallback, retry, circuit-breaker, cost, and latency
  planning.
- Model-gateway guard decisions.
- Provider-adapter protocol with no live-send operation.
- Deterministic reference provider for text and structured JSON simulation.
- Restricted structured-output schemas.
- Response validation, untrusted-output classification, provenance, audit,
  observability, health, integrity, diagnostics, and operator-review evidence.

The only provider is `deterministic-reference-provider`. The only models are
`reference-text-sim-v1` and `reference-json-sim-v1`. No external model provider
is called. No network egress, provider SDK, credential read, token persistence,
authorization header, live model session, connector, tool, function, shell,
subprocess, browser, module activation, prompt persistence, response
persistence, memory write, belief mutation, source rewrite, deployment, or
model training is enabled.
