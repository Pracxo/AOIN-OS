# 0037: Local Release Package Handoff

## Status

Accepted

## Context

AION Brain v0.1 needs a final local handoff artifact after release baseline,
version manifest, compatibility matrix, migration baseline, release artifact
metadata, and freeze gate checks exist. The handoff must be useful before any
cloud deployment, production auth, frontend work, or domain module exists.

## Decision

Add a local release package backend owned by AION Brain. It produces
frontend-agnostic and provider-neutral package contracts, a source manifest,
checksums, generated report artifacts, a placeholder SBOM, persisted package
records, and a handoff report.

Keep release packaging local-only in v0.1. The API service must not call shell
scripts, Docker, package registries, cloud storage, external observability
services, external network services, optional adapters, or domain modules.

Keep the SBOM as a placeholder until a future task adds a real SBOM adapter.
AION public contracts must not depend on any future SBOM tool internals.

## Consequences

Future frontend, deployment, or marketplace workflows can consume the release
package contracts without changing Brain core. Local developers can validate a
release package with deterministic checksums and a handoff report before any
production deployment exists.

The package is not a production certification. It is a local v0.1 handoff
artifact that records current limits and exact local verification commands.

## Constraints

- No cloud upload in v0.1.
- No subprocess or Docker execution in the API packager.
- No external network calls.
- No domain-specific release logic.
- No raw secrets, env files, caches, virtualenvs, `.aion_objects`, or
  `.aion_indexes` in package artifacts.
