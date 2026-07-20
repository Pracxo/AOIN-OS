# Shadow-Mode Evaluation Scenarios

AION-179 evaluates fourteen read-only scenarios:

- no-pattern
- repeated-retrieval-failure
- planning-failure
- evidence-grounding-failure
- policy-violation
- budget-violation
- missing-reference
- fingerprint-mismatch
- protected-input-rejection
- output-boundary
- deterministic-replay
- retention
- bounded-concurrency
- runtime-influence-boundary

All scenarios must pass for the PASS recommendation. A single scenario failure
forces `SHADOW_MODE_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED`.

The scenarios cover both positive advisory evidence and fail-closed behavior:
budget overrun, missing references, fingerprint mismatch, rejected protected
inputs, output-directory rejection, deterministic replay, explicit retention
purge, bounded concurrency, and zero runtime influence.
