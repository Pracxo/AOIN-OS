# ADR 0025: Attention Controller, Working Memory, and Focus Manager

## Decision

AION Brain adds an Attention Controller and Working Memory Stack for v0.1.

The Context Compiler consumes `AttentionDecision` and `ContextBudget`; it does not own focus. The Retrieval Router retrieves candidate context; it does not decide what deserves attention. Working memory is short-lived cognitive state and remains separate from long-term semantic, graph, and evidence storage.

Attention scoring is deterministic in v0.1. AION does not use LLM-based attention scoring and does not store chain-of-thought in working memory.

## Reason

AION needs cognitive focus before stronger autonomy and multi-task operation. Future modules can emit signals, but AION core decides focus, interruptions, and context budget allocation.

## Consequences

Focus sessions preserve continuity across task and workflow boundaries. Working memory can carry compact references to events, goals, tasks, memories, evidence, skills, capabilities, and traces. Context budgets reduce context pollution before fusion.

## Constraints

No domain-specific priority logic is allowed in Brain core. No external calls are made by the attention layer. Working memory is not a truth store and is not chain-of-thought storage.
