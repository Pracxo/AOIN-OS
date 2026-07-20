# Shadow-Mode Pipeline

`ControlledShadowPipeline` runs one explicit manifest at a time. Its injected
collaborators are the reference adapter, resource budget, clock, monotonic
clock, and ID factory.

The deterministic order is:

1. Validate manifest and lineage.
2. Enforce pre-resolution budgets.
3. Resolve references through the injected read-only adapter.
4. Validate redacted snapshots.
5. Build observations.
6. Evaluate metrics.
7. Mine repeated failure patterns.
8. Generate bounded hypotheses.
9. Generate regression-test specifications.
10. Generate shadow proposal candidates.
11. Project operator review items.
12. Enforce post-generation budgets.
13. Emit diagnostics, audit, provenance, and bundle evidence.

If no repeated pattern exists, the run completes without candidates. If a
reference fails, the run fails closed without fallback. If a budget fails, the
run returns no partial candidates and records a redacted budget-failure record.
