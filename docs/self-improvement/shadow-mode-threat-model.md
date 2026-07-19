# Shadow-Mode Threat Model

Primary risks:

- Accidental source mutation through a shadow pipeline.
- Hidden activation of Git, branch, PR, merge, or deployment behavior.
- Sensitive data exposure through observation evidence.
- Policy bypass through a trusted internal self-improvement path.
- Resource exhaustion through unbounded observations.
- Confusion between operator evaluation and implementation approval.

Required mitigations:

- Fail closed when runtime enablement flags are not explicitly false.
- Enforce zero budgets for source changes, Git writes, provider calls, network
  calls, PR creation, and merges.
- Redact evidence before persistence.
- Keep each operator-visible review item advisory and non-approving.
- Require human approval and exact future authorization before any source change.
- Preserve immutable `aion-v0.1.0` and absence of v0.2 tags and releases.

Residual risk remains until AION-178 has source-level tests for the disabled
shadow pipeline. AION-177 does not implement that pipeline.
