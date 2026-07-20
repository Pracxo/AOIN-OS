# Shadow-Mode Security Review

AION-178 preserves the AION-177 boundary: observation-only, redacted,
operator-invoked, and runtime-disabled.

Security controls:

- recursive rejection of protected input markers
- UTC-only timestamp validation
- lowercase SHA-256 fingerprint validation
- strict extra-field rejection
- zero side-effect budgets
- output directory escape prevention
- immutable evidence models
- deterministic replay checks
- no protected-controller imports
- no network, connector, provider, source, Git, PR, approval, merge, canary,
  deployment, promotion, or model-training integration

The implementation does not change protected self-improvement controllers,
policy, audit, security, kernel, API, SDK runtime surfaces, workflows,
dependencies, migrations, `aion-v0.1.0`, or any v0.2 tag or release.
