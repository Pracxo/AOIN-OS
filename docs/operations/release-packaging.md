# Local Release Packaging

AION v0.1 release packaging is local-only. It produces a handoff bundle under
`artifacts/releases/` by default and persists package metadata in the Brain API.

The packager includes:

- source manifest
- contract export metadata
- policy bundle metadata
- migration baseline metadata
- release baseline metadata
- freeze gate metadata
- compatibility metadata
- release artifact metadata
- checksum manifest
- SBOM placeholder
- handoff report

The API path does not call shell scripts, Docker, package registries, cloud
storage, external observability services, or external network services.

## API

- `POST /brain/release-package/create`
- `GET /brain/release-package/{release_package_id}`
- `GET /brain/release-package`
- `POST /brain/release-package/{release_package_id}/validate`
- `GET /brain/release-package/{release_package_id}/handoff`

## Local Commands

```bash
./scripts/aionctl.sh --scope workspace:main release package --version 0.1.0 --dry-run
./scripts/aionctl.sh --scope workspace:main release package --version 0.1.0 --write
./scripts/package-release.sh
./scripts/verify-release-package.sh
```

`scripts/package-release.sh` requires the local Brain API to be reachable. If it
is not reachable, it prints:

```text
AION server is not reachable. Start core stack first.
```

## Checksums

Each included release package file has a SHA-256 checksum. The root checksum is
deterministic and order-independent. `scripts/verify-release-package.sh` checks
the latest local package directory for `release-package-manifest.json` and
`checksums.json`, then verifies any generated package files it can find.

## SBOM Placeholder

The SBOM placeholder reads only local project metadata. It does not resolve
transitive dependencies, query package registries, upload artifacts, or claim to
be a production SBOM.

## Exclusions

Release packages must exclude `.env` files, cache directories, virtual
environments, `.aion_objects`, `.aion_indexes`, raw secrets, and secret-like
file names.
