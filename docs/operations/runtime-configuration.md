# Runtime Configuration Control Plane

AION v0.1 runtime configuration is a local control plane for inspecting safe
configuration metadata, feature flag overrides, validation posture, and
configuration drift.

It is not a secrets system, cloud parameter store, or production configuration
manager. Environment variables remain the boot-time source of truth.

## Boot-Time Source

Process environment variables are read by `Settings` when the Brain API starts.
The runtime configuration API does not mutate operating system environment
variables and does not hot-reload process settings in v0.1.

Runtime records store safe metadata about intended behavior, active profiles,
feature override state, and redacted snapshots.

## Config Profiles

Config profiles describe named local configuration postures. They can record
safe values, feature flags, constraints, and metadata for development,
test, release-candidate, or custom use.

Activating a profile marks metadata as active for inspection. It does not
rewrite `.env`, mutate the running process, or enable unsafe defaults.

## Feature Flag Overrides

Feature flag overrides let operators locally adjust generic AION feature state
through policy-gated records. Overrides must reference generic feature keys from
the feature registry when the registry is available.

Overrides cannot enable full autonomy, external tools, external models, or other
unsafe defaults in v0.1.

## Config Snapshots

Snapshots capture:

- redacted `Settings` metadata
- effective feature flags
- adapter status
- deterministic configuration hash
- optional drift from a previous snapshot

Sensitive setting keys are allowed only when their values are redacted metadata.
Raw secret values are never stored.

## Config Validation

Validation checks local posture for safe defaults, no raw secret values,
disabled external model defaults, disabled MCP defaults, disabled sandbox
execution, disabled restore apply, disabled outbox processing, stacktrace
exposure, optional adapter warnings, and unsafe feature overrides.

The validator returns `passed`, `warning`, or `failed` and stores a local
validation run for status, freeze gate, security baseline, and release metadata.

## Drift Detection

Drift detection compares two redacted snapshots and reports added, removed, and
changed keys across settings, feature flags, and adapter status.

Drift is metadata-only. It does not apply changes.

## Safe Defaults

Runtime configuration is policy-gated and fail-closed. Safe defaults require:

- no full autonomy by default
- no external tools or external models by default
- no raw secrets in records, logs, tests, telemetry, or docs
- no process environment mutation from API routes
- no domain-specific config keys

## Local Commands

```bash
./scripts/config-snapshot.sh
./scripts/config-validate.sh
./scripts/aionctl.sh --scope workspace:main config status
./scripts/aionctl.sh --scope workspace:main config validate
./scripts/aionctl.sh --scope workspace:main config snapshot
```

