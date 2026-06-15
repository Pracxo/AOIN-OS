# ADR 0018: Model Gateway Provider Registry and Budget Guard

## Decision

AION Brain adds a provider-neutral Model Gateway. The deterministic provider
remains the default profile and fallback. External model calls are disabled by
default. LiteLLM-compatible and OpenAI-compatible HTTP integrations stay behind
`ModelGatewayAdapter` boundaries. Public AION contracts never expose provider
SDK objects, raw provider responses, API keys, auth headers, or vendor-specific
types.

## Reason

AION needs a real inference path later without provider lock-in. Provider and
profile registries let future model choices be governed through contracts,
policy, privacy level, risk level, budget, and health instead of hard-coded
vendor assumptions.

## Consequence

Stronger models can be added later by registering providers and profiles. The
Reasoning Mesh remains stable because it talks to `ModelGatewayService`, not
provider SDKs. Prompt redaction, model budget checks, model usage records, and
telemetry are enforced before any external completion can occur.

## Constraints

No external model calls occur in tests. External calls require explicit
settings, `allow_external=true`, policy permission, and budget approval. v0.1
does not import provider SDKs. No domain-specific reasoning logic is allowed in
the gateway.
