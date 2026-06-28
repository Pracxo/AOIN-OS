# Action Authorization Preview

The static Operator Console includes an Action Authorization panel backed by:

- `operator-console-static/demo-data/action-authorization-preview.json`
- `operator-console-static/demo-data/action-authorization-deny-matrix.json`

The panel renders decision, status, role, policy, and session booleans. It also
shows the dry-run boundary flags:

- `dry_run_only=true`
- `write_allowed=false`
- `execution_allowed=false`
- `activation_allowed=false`
- `external_calls_allowed=false`

There is no authorize-to-execute button, activation button, external-call
button, credential input, or browser storage.
