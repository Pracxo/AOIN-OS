# Secure Runtime Audit And Observability

AION-231 may emit redacted local audit and observability evidence for the
operator. Evidence is read-only and must not include credentials, tokens,
private keys, raw authentication material, raw request bodies, hidden reasoning,
or protected material.

## Audit Records

Audit records bind:

- operator invocation
- identity assertion verification result
- request identity projection
- ActorContext binding
- replay validation
- session state transitions
- policy, risk, and guardrail decisions
- approval evidence fingerprints
- side-effect budget counters
- runtime guard decision
- kill-switch state
- simulated dispatch result
- session close

## Observability

Observability snapshots may expose health, readiness, counters, trace IDs,
stage counts, terminal state, and redacted findings. They must not expose
credential, token, private-key, or protected material values.
