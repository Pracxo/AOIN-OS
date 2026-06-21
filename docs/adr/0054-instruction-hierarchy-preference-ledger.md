# ADR 0054: Instruction Hierarchy and Preference Ledger

## Status

Accepted.

## Decision

AION Brain adds an Instruction Hierarchy and Preference Ledger for v0.1.
Instructions, preferences, constraints, style profiles, conflicts, preference
candidates, and resolution runs are represented as AION-owned contracts.

Preferences do not override policy, autonomy, approval requirements, runtime
configuration, capability limits, sandbox limits, or hard safety constraints.
Learned preferences are candidates until explicitly confirmed. Conflict
detection and resolution are deterministic in v0.1.

## Reason

AION needs consistent instruction handling across dialogue, context
compilation, response composition, operator review, telemetry, SDKs, and future
modules. Without a canonical hierarchy, clients could accidentally treat style
or preference as permission.

## Consequences

Future UI and module clients can provide preferences without owning
instruction precedence. The resolver can shape context and response metadata
without expanding permissions or executing actions.

## Constraints

AION must not store hidden prompts, chain-of-thought, raw secrets, or
domain-specific preferences in Brain core. Instruction resolution remains
Brain-only, deterministic, policy-gated, and adapter-neutral.
