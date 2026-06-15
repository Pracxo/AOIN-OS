# AION Versioning

AION Brain v0.1 uses a local version manifest to freeze the public Brain
surface before later modules depend on it. The manifest records the release
version, API version, SDK version, schema version, contract hash, feature
flags, adapter matrix, and release metadata.

The versioning layer is Brain-only and generic. It does not package artifacts,
upload files, call external services, execute shell commands, or encode
vertical workflows. It records release-readiness metadata that can be queried
through public AION APIs and the Python SDK.

## Contracts

- `VersionManifest` records the version, release channel, feature flags,
  adapter matrix, and contract hash.
- `FeatureRegistryEntry` records generic feature keys, status, category,
  default enablement, required flags, dependencies, and owner scope.
- `CompatibilityMatrix` records local runtime compatibility and optional
  adapter status.
- `MigrationBaseline` records migration count, hash, table inventory, and
  destructive migration findings.
- `ReleaseArtifactManifest` records metadata-only release artifacts and
  checksums.
- `SDKCompatibilityReport` records SDK/API resource compatibility.
- `FreezeGateRun` records the deterministic freeze gate result.

## Feature Registry

Feature keys are generic dotted or underscored identifiers such as
`kernel.container`, `memory.lexical`, `visual.projection`, `sdk.python`, and
`ci.quality_gates`. Feature records reject vertical domain terms and
secret-like metadata. Defaults can be dry-run inspected or persisted locally.

## Freeze Flow

1. Seed or inspect the generic feature registry.
2. Create a `VersionManifest`.
3. Generate compatibility, migration, and release artifact records.
4. Run the freeze gate.
5. Freeze the manifest only after a passed freeze gate exists for that version.

## API

- `POST /brain/versioning/manifests`
- `GET /brain/versioning/manifests/{version}`
- `GET /brain/versioning/manifests`
- `POST /brain/versioning/manifests/{version}/freeze`
- `POST /brain/versioning/features/seed-defaults`
- `GET /brain/versioning/features`
- `POST /brain/versioning/features`
- `POST /brain/versioning/features/{feature_key}/deprecate`
- `POST /brain/versioning/compatibility/generate`
- `GET /brain/versioning/compatibility/{version}`
- `POST /brain/versioning/migration-baseline/generate`
- `POST /brain/versioning/release-artifacts/generate`
- `GET /brain/versioning/sdk-compatibility`
- `POST /brain/freeze-gate/run`
- `GET /brain/freeze-gate/{freeze_gate_id}`
- `GET /brain/freeze-gate`

## CLI

```bash
./scripts/aionctl.sh --scope workspace:main versioning manifests create --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning features seed-defaults
./scripts/aionctl.sh --scope workspace:main versioning compatibility generate --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning migration-baseline --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning release-artifacts --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning sdk-compatibility
./scripts/aionctl.sh --scope workspace:main freeze run --version 0.1.0
```

The CLI calls public Brain HTTP APIs through the SDK only.
