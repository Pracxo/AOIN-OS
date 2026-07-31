# Model Gateway Security Review

AION-233 keeps the model gateway provider-neutral, credential-free,
network-disabled, and simulation-only. The gateway composes AION-231 through
`brain.think.simulate`, requires parent guard outcome `allow_simulation`, and
requires parent simulated dispatch status `simulated`.

Security controls:

- Only `deterministic-reference-provider` is allowed.
- Only `reference-text-sim-v1` and `reference-json-sim-v1` are allowed.
- Provider and model manifests are immutable and endpoint-free.
- Request envelopes retain fingerprints and budgets, not raw prompt bodies.
- Prompt protected material is rejected before routing.
- Context and token over-limit values fail closed.
- Routing, fallback, and retry are planning evidence only.
- Circuit-breaker transitions are explicit and local.
- The provider adapter exposes no live-send, connect, stream, authenticate,
  credential, tool, or function operation.
- Responses are validated, redacted, provenance-bound, and classified
  untrusted.
- Audit, observability, health, integrity, and pilot evidence remain redacted.

No model output becomes factual truth, approval evidence, memory, belief,
policy, action trigger, connector request, tool request, deployment decision,
or successor authorization. AION-232-SRI-0002 remains active for AION-234
formal evaluation and closeout.

## AION-234 Closeout

`AION-SRIPE-002` passed all 28 model-gateway operator-evaluation scenarios. `AION-232-SRI-0002` is closed, consumed, expired, and non-reusable. `AION-234-SRI-0003` is active for AION-235 only. AION-235 is authorized to implement a sandboxed deterministic capability and synthetic connector runtime, but no AION-235 source is present in this closeout. Model output remains untrusted and cannot trigger execution. External connectors, real tools, network, credentials, filesystem, process, production runtime, v0.2 tags, and v0.2 releases remain disabled.
