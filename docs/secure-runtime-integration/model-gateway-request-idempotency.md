# Model Gateway Request Idempotency

Request envelopes bind the gateway session, parent secure-runtime request, parent capability plan fingerprint, ActorContext binding fingerprint, closed provider/model allowlists, system policy fingerprint, message/context fingerprints, budget decision fingerprints, structured schema fingerprint, output mode, requested output tokens, safe metadata fingerprint, timestamps, and no-effect flags.

Exact replay returns the existing safe result fingerprint. Changed replay against the same session-scoped request ID is rejected. Cross-session replay is not accepted.
