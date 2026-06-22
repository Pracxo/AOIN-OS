# ADR 0036: Version Manifest, Compatibility Matrix, and Freeze Gate

## Status

Accepted.

## Context

AION Brain v0.1 needs a stable release boundary before later modules, optional
adapters, and external runtimes depend on it. The Brain already owns public
contracts, release baseline scenarios, SDK paths, and kernel diagnostics, but
it needs an explicit manifest and freeze gate to record what is releasable.

## Decision

AION Brain will own a backend-only versioning and freeze-control layer:

- `VersionManifest` records version, channel, API, SDK, schema, contract hash,
  feature flags, and adapter matrix.
- `FeatureRegistryEntry` records generic Brain feature status.
- `CompatibilityMatrix` records local component and optional adapter status.
- `MigrationBaseline` records migration hash, table inventory, and destructive
  migration findings.
- `ReleaseArtifactManifest` records metadata-only artifact checksums.
- `FreezeGateRun` records deterministic local freeze checks.

The freeze gate runs through services and adapters only. It does not call shell
scripts, Docker, external observability services, optional adapters, or domain
modules. SDK and CLI access goes through public HTTP APIs.

## Consequences

Future releases can freeze a contract hash, feature set, migration baseline,
and compatibility matrix before modules depend on them. Optional adapters stay
replaceable because versioning records their availability without making their
SDK objects public AION contracts.

## Constraints

- No domain-specific feature keys or release checks.
- No raw secrets in contracts, fixtures, telemetry, or release artifacts.
- No external service calls in v0.1 freeze checks.
- Full autonomy remains disabled by default.
- Versioning contracts remain frontend-, provider-, and framework-neutral.
