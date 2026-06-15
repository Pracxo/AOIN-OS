# ADR 0008: Reasoning Mesh and Model Gateway Boundary

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain uses a Reasoning Mesh as the single core boundary for generic
reasoning. The mesh owns prompt packets, model route decisions, reasoning
results, model call ledger records, policy checks, audit references, and visual
telemetry.

Model inference must happen only through `ModelGatewayAdapter`. In v0.1 the
only implementation is `DeterministicReasoningAdapter`, which selects
`aion-local` / `deterministic-reasoner-v0` and makes no external calls.

## Reason

Reasoning needs a contract before AION uses real providers. Owning the
reasoning packet and ledger now prevents future providers from leaking their SDK
objects, runtime types, or private semantics into Brain public APIs.

## Constraints

- No external model provider calls in v0.1.
- No OpenAI, Anthropic, Gemini, Ollama, LiteLLM, or local runtime SDK objects in
  public contracts.
- LiteLLM remains a placeholder adapter only.
- Model routing is policy-gated and local-provider-only in v0.1.
- Reasoning remains domain-neutral.

## Consequences

AION can later replace or extend the model gateway without changing public Brain
contracts. Reasoning runs and model calls are audit-ready from the beginning,
and the deterministic v0.1 loop remains testable without Docker or provider
credentials.
