# Shadow-Mode Operator Runbook

Operators may run AION-178 through the explicit Python API by supplying a
manifest, immutable redacted snapshots, and an optional output directory. The
runner is not installed as a CLI and is not connected to production runtime
traffic.

Expected operator evidence:

- `ShadowEvidenceBundle`
- `ShadowRunDiagnostics`
- `ShadowOperatorReviewItem`
- budget decision and optional budget-failure record
- deterministic fingerprints

Any operator review item is advisory. It cannot approve work, satisfy an
approval record, create a branch, create a pull request, merge code, promote a
candidate, or enable production shadow mode.

## AION-179 Operator Evaluation

Run the closeout gate after reviewing the machine report:

```sh
./scripts/self-improvement-shadow-mode-operator-evaluation-no-go-regression.sh
./scripts/self-improvement-shadow-mode-operator-evaluation-check.sh
```

The PASS recommendation remains review-only. Operators must treat runtime
activation as blocked until a separate future authorization exists.
