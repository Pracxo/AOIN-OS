# 0050: Outcome Ledger, Effect Verification, and Learning Feedback Bridge

## Status

Accepted.

## Decision

AION Brain records expected effects, observed effects, outcome records,
verification runs, causal attributions, and outcome feedback in a local Outcome
Ledger.

Effect verification is deterministic. It compares AION-owned expected effects
against AION-owned observed effects and can update outcome status only in
controlled mode. Dry runs persist verification metadata without mutating source
records.

The learning bridge creates reviewable outcome feedback. It does not promote
skills, rewrite memory, execute remediation, call model providers, or call
external observability services.

## Reason

AION needs a durable way to answer: what did we expect, what did we observe,
was the effect verified, and what feedback should future learning review?

## Consequences

Commands, workflows, decisions, counterfactuals, plans, and module
certification can attach generic effect and outcome records without coupling to
domain workflows. Operator views can surface failed outcomes and feedback.
Visual telemetry can project outcome activity into the Brain Map.

## Constraints

- Outcome verification is not proof of truth.
- Completion is not verification.
- Outcome services never mutate source records.
- Outcome feedback never auto-promotes skills.
- AION core outcome contracts remain generic and domain-neutral.
- No external network calls are required for v0.1 outcome verification.
