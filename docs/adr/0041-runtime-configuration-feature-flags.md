# 0041: Runtime Configuration and Feature Flags

## Status

Accepted

## Decision

AION Brain v0.1 adds a Runtime Configuration Control Plane.

Environment variables remain the boot-time configuration source. The runtime
configuration API stores safe configuration metadata, feature flag overrides,
redacted snapshots, validation runs, and drift reports only.

Runtime configuration does not store raw secrets and does not mutate process
environment variables in v0.1.

## Reason

AION needs inspectable configuration before broader use. Operators and local
developer workflows need to see effective feature state, safe default posture,
snapshot hashes, and drift without editing source code or introducing cloud
configuration dependencies.

## Consequence

The freeze gate and security baseline can validate effective configuration.
Version manifests can include effective feature flags, the active profile name,
and a configuration hash. The SDK and `aionctl` can inspect and request safe
runtime configuration records through public APIs.

## Constraints

- No raw secrets in runtime configuration records.
- No process environment mutation from runtime configuration APIs.
- No cloud configuration backend in v0.1.
- No unsafe defaults enabled through feature overrides.
- No domain-specific configuration keys or policy.

