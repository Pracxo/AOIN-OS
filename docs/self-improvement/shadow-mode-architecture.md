# Controlled Self-Improvement Shadow-Mode Architecture

AION-177 authorizes AION-178 to implement controlled shadow-mode architecture
only. The authorized design is observation-only: it may read approved synthetic
or redacted evidence, derive bounded hypotheses, compare policy decisions, and
produce review records for an operator.

Shadow mode must not mutate source, run Git writes, create branches, create pull
requests, merge code, deploy, activate production canaries, call model
providers, call connectors, or train model weights.

Authorized components for AION-178:

- Shadow-mode contracts.
- Shadow observation record.
- Shadow pipeline coordinator.
- Shadow evidence redaction boundary.
- Shadow resource budget enforcement.
- Shadow output boundary.
- Operator review item projection.

The architecture remains behind the disabled governed self-improvement platform.
`shadow_mode_authorized=true` records scope approval. It does not imply
`shadow_mode_implemented=true`, and it must not imply
`shadow_mode_runtime_enabled=true`.
