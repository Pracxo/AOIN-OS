# Model Gateway Output Provenance Implementation

AION-233 records output provenance as redacted control-plane evidence. The
provenance binds provider ID, provider manifest fingerprint, model ID, model
manifest fingerprint, request fingerprint, route-plan fingerprint, response
fingerprint, validation-result fingerprint, output classification, redaction
state, audit-chain head, and timestamps.

Provenance does not retain raw prompt text, raw context, raw response bodies,
provider raw payloads, hidden reasoning, credentials, tokens, authorization
headers, tool calls, function calls, connector requests, or production actions.

The provenance record confirms that the deterministic reference-provider output
is synthetic and untrusted. It is review evidence only and does not authorize
memory writes, belief changes, policy changes, source changes, deployment, or
model training.
