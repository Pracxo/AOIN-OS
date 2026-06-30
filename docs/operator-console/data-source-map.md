# Operator Console Data Source Map

The data-source map links future console views to existing Brain services and
API/CLI hints. It does not execute those hints. It only describes where a future
operator could inspect state.

## Views

- `overview`: operator overview, health, readiness, notifications, incidents
- `readiness`: bootstrap, setup doctor, Golden Path, release smoke
- `release_candidate`: RC gate, reports, findings, evidence
- `freeze_release`: freeze gate, release package, release baseline
- `golden_path`: Golden Path runs and reports
- `module_lifecycle`: extensions, bindings, conformance, readiness, activation
  gate metadata, mock runtime metadata
- `module_activation`: activation gate metadata and blockers
- `module_mock_runtime`: mock runtime metadata and findings
- `model_provider_hardening`: provider profiles, prompt egress preview,
  simulation metadata, readiness, blockers
- `notifications`: notifications, alerts, escalations, digests
- `incidents`: incident signals, records, root-cause candidates, reviews
- `registry_integrity`: resource registry, link validation, snapshots
- `lifecycle_review`: policies, classifications, archive candidates, redaction
  candidates, purge previews
- `audit_provenance`: audit entries and provenance links
- `settings_safety`: runtime config, security baseline, feature flags
- `connector_sandbox`: connector sandbox boundary, capability rules, readiness
  preview, and no-go evidence

## Safety

Every source is read-only. Missing optional services produce unavailable
sections instead of crashing. Source metadata must not contain credentials,
private reasoning text, provider payloads, or source prompts.
