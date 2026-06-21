# ADR 0057: Model Output Governance

## Status

Accepted.

## Context

AION already governs prompts and model input manifests before a provider or
deterministic adapter is called. The next boundary is model output intake.
Provider output must become an AION-owned, redacted, hashed, auditable contract
before any response candidate, tool intent, telemetry, or operator surface can
consume it.

## Decision

Add a Model Output Governance layer with provider-neutral contracts for model
outputs, parsed segments, structured-output validation, response candidates,
tool intent candidates, governance runs, and query results.

The layer stores a hash of raw output and a redacted output body. Raw model
output is not stored by default. Structured parsing and validation are
deterministic. Tool intents are captured but not executed. Response candidates
remain local drafts until explicitly promoted through policy and response
verification.

The Model Gateway calls output governance after completion and returns only
governance identifiers and status metadata.

## Consequences

- AION can audit model outputs without exposing provider SDK objects.
- Future response delivery can consume governed response candidates instead of
  raw model payloads.
- Operator surfaces can review blocked outputs, response candidates, and tool
  intents.
- Visual telemetry can project model output governance without frontend
  coupling.

## Constraints

- Do not store raw model outputs by default.
- Do not store or expose hidden reasoning, chain-of-thought, raw prompts, raw
  headers, provider payloads, or secrets.
- Do not execute model-suggested tool intents.
- Do not add provider-specific output contracts.
- Do not add domain-specific output governance rules.
- Do not call external services from v0.1 output governance.
