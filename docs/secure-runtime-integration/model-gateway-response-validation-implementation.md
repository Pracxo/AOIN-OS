# Model Gateway Response Validation Implementation

AION-233 validates every deterministic reference-provider response before it is
retained as evidence. Validation binds the request fingerprint, provider and
model manifest fingerprints, route-plan fingerprint, output mode, response byte
limit, estimated output-token limit, and structured-output schema when present.

Response validation rejects protected material, tool-call smuggling,
function-call smuggling, executable-content injection, hidden-reasoning
markers, provider raw-payload markers, production-action markers, and output
size violations. Validation errors are redacted and do not echo rejected
content.

A passing response remains untrusted. It has no factual, approval, memory,
belief, policy, connector, tool, production, or runtime effect.
