# Shadow-Mode Operator Evaluation Report

`AION-SOE-001` ran the AION-178 public Python API against synthetic, redacted,
read-only references and metrics.

The harness used these AION-178 objects only:

- `ShadowObservationManifest`
- `ShadowReference`
- `ShadowRedactedMetric`
- `ShadowReferenceSnapshot`
- `InMemoryShadowReferenceAdapter`
- `ShadowResourceBudget`
- `ControlledShadowPipeline`
- `ControlledShadowModeRunner`
- `replay_shadow_run`
- `EphemeralShadowStore`

The report records a PASS decision because every hard gate and every scenario
passed. Repository digest before and after the harness run matched, and the
temporary output directory was outside the repository.

The full machine-readable report is
`examples/self-improvement/shadow-mode-operator-evaluation-report.json`.
