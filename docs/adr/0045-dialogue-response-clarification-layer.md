# ADR 0045: Dialogue Response and Clarification Layer

## Status

Accepted

## Decision

AION Brain adds a backend-only Dialogue Session Manager, deterministic Response
Composer, Response Verifier, Clarification Loop, and Dialogue Memory Handoff
boundary.

Dialogue contracts are AION-owned and provider-neutral. They do not expose chat
provider message objects, frontend state, transport-specific delivery handles,
raw prompts, chain-of-thought, or hidden reasoning.

## Reason

AION needs a stable conversational boundary before UI, external model calls, or
controlled execution can be layered on top. Dialogue turns must produce normal
Brain artifacts: sanitized messages, policy decisions, traces, response drafts,
clarification requests, local delivery records, feedback records, visual
telemetry, audit provenance, and optional memory handoff candidates.

## Consequences

Future interfaces can call the same dialogue and response APIs without coupling
to a frontend framework. Future model providers can participate through the
existing model and reasoning boundaries, while responses remain AION contracts.

Clarification remains a first-class Brain loop outcome. When intent, context,
policy, grounding, or confidence is insufficient, AION records a clarification
request instead of guessing or executing.

## Constraints

- v0.1 does not implement a frontend chat UI.
- v0.1 does not call external model providers from the dialogue layer.
- v0.1 does not send messages to external delivery channels.
- Dialogue turns cannot trigger controlled execution.
- Raw prompts, chain-of-thought, hidden reasoning, raw headers, and secrets must
  not be persisted.
- Memory handoff is optional, policy-gated, and stores summaries or references,
  not raw sensitive content.
- Dialogue policy actions remain generic and domain-neutral.
