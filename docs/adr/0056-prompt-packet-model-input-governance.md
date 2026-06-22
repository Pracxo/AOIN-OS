# 0056: Prompt Packet and Model Input Governance

## Status

Accepted

## Context

AION Brain now has instruction, grounding, dialogue, response, reasoning,
planning, model gateway, audit, provenance, operator, and visual telemetry
layers. These layers need one provider-neutral way to compile safe model input
without exposing raw prompts, hidden reasoning, or provider-specific prompt
objects.

## Decision

AION adds a Prompt Packet Compiler and Model Input Governance layer.

Prompt packets are provider-neutral AION contracts. They are not OpenAI,
Anthropic, LiteLLM, MCP, or frontend payloads.

Retrieved context is untrusted context unless another governed AION contract
explicitly marks it otherwise. Memory recall must be labeled as memory recall
because it is not canonical truth.

Raw rendered prompts are not persisted by default. Prompt packet storage keeps
section manifests, hashes, redacted previews, constraints, and metadata.

Prompt injection detection is deterministic in v0.1. It uses local string and
regex checks only and does not call model providers or external classifiers.

## Reason

AION needs governed model input boundaries before broader model routing. A
shared packet contract lets Reasoning, Dialogue, Planning, Response, and Model
Gateway components agree on safe prompt semantics while keeping model providers
behind adapters.

## Consequences

Reasoning, Dialogue, Planning, Response, and Model Gateway can share safe prompt
packet semantics. Operator, audit, provenance, visual telemetry, SDK, and CLI
surfaces can inspect prompt governance metadata without raw prompt exposure.

Future provider adapters can consume `PromptPacket` and `ModelInputManifest`
without changing public Brain contracts.

## Constraints

- Do not store hidden reasoning.
- Do not expose raw prompts.
- Do not persist raw rendered prompts by default.
- Do not introduce provider-specific prompt contracts.
- Do not add domain-specific prompt packs to Brain core.
- Do not call external AI services from prompt compilation or boundary checks.
