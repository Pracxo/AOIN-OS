# Shadow-Mode Evidence

AION-178 evidence is immutable, redacted, and advisory. Evidence bundles include
audit events, provenance, diagnostics, resource budget, resource usage, budget
decision, optional budget-failure evidence, observations, evaluation summary,
failure-pattern candidates, hypotheses, regression-test specifications, shadow
proposal candidates, and operator review items.

Every evidence object keeps `runtime_effect=false`, `source_modified=false`,
`git_mutated=false`, `pull_request_created=false`, `approval_created=false`,
`merged=false`, and `active_learning_promoted=false`.

Fingerprints use canonical JSON and exclude each object's own fingerprint
field. Changing safety-relevant fields changes the fingerprint.
