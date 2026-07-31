# Model Gateway Observability Implementation

AION-233 provides redacted observability and health snapshots for the local
simulation gateway. Observability records counts, fingerprints, readiness
state, audit-chain head, and prohibited-effect counters.

Snapshots never include raw prompt bodies, raw context, raw response bodies,
hidden reasoning, provider raw payloads, credentials, API keys, tokens,
authorization headers, tool calls, function calls, connector requests, or
temporary paths.

Health readiness requires exact `AION-232-SRI-0002` authorization, valid
AION-231 secure-runtime binding, clear parent kill switch, closed provider and
model registries, deterministic reference-provider availability, valid budgets,
disabled provider calls, disabled network egress, disabled credentials,
disabled tools, disabled connectors, and disabled production runtime.
