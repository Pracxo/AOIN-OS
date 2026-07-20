# Shadow-Mode Operator Workflow

Authorized AION-178 workflow:

1. Load synthetic or redacted observation input.
2. Apply resource budgets before producing any candidate hypothesis.
3. Compare the proposed policy posture against current disabled-runtime policy.
4. Emit a redacted review item with an observation ID, hypothesis summary,
   policy delta summary, risk level, budget status, and operator-review flag.
5. Stop.

Permitted review states:

- `shadow_observed`
- `shadow_evaluated`
- `shadow_pattern_detected`
- `shadow_hypothesis_generated`
- `shadow_regression_proposed`
- `shadow_proposal_generated`
- `operator_review_pending`
- `discarded`
- `archived`

Forbidden review states:

- `approved`
- `pr_created`
- `merged`
- `canary`
- `promoted`

Any later source-changing work requires a separate explicit approval record and
must not reuse AION-177.
## AION-178 Operator Workflow Update

Operators can invoke the controlled shadow plane only by supplying a manifest
and read-only redacted reference snapshots to the Python runner. The default
run writes no files. Optional output requires an existing absolute directory
outside the repository. Operator review items remain advisory and expire under
the retention limit.
