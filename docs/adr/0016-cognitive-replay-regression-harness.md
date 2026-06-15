# ADR 0016: Cognitive Replay and Regression Harness

## Status

Accepted

## Decision

AION Brain adds a Cognitive Replay and Regression Harness. Brain snapshots use
deterministic content hashes, and v0.1 comparison is local and deterministic.
Promptfoo and Ragas remain behind placeholder evaluation adapters.

## Reason

AION needs reproducibility before external model integration. Completed Brain
traces must become stable evidence that architecture and policy changes can be
checked against.

## Consequences

- Codex changes can be checked against golden traces.
- Semantic drift is visible without an LLM judge.
- Replay and regression records remain AION-owned public contracts.
- External evaluation systems can be introduced later without changing those
  contracts.

## Constraints

- No external evaluation tools are called in v0.1.
- Replay mode cannot create external side effects.
- No subprocess or external model call is used.
- No domain-specific regression logic belongs in Brain core.
