# ADR 0048: Situation Model and Temporal State Projection

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain adds a backend Situation Model, Temporal State Projection layer, and
Context Continuity record path.

The layer owns generic contracts for `SituationRecord`, `StateAtom`,
`TemporalStateWindow`, `StateTransition`, `SituationProjectionResult`, and
`ContextContinuityRecord`.

## Reason

AION needs a deterministic answer to "what is currently going on" before later
reasoning, retrieval, dialogue, and operator surfaces can coordinate around
current context.

## Constraints

- Situation projection is recall, not truth.
- State atoms are projected observations and never mutate source records.
- No LLM summarization is used.
- No domain-specific state model is introduced.
- Controlled projection must pass policy and autonomy boundaries.
- Public contracts remain AION-owned and do not expose SQLAlchemy rows or
  vendor-specific objects.

## Consequences

Future context compilation can include current situations, stale state warnings,
continuity drops, and temporal windows without coupling the Brain to a
frontend, a model provider, or a vertical workflow.
