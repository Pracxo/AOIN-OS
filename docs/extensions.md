# Extension Registry and Module Intake

AION v0.1 Extension Registry is a metadata-only intake layer for future Brain
extensions. It accepts local manifests, validates declared metadata, records
package records, capability declarations, dependency declarations,
compatibility checks, reviews, and future install plans.

The registry does not load code, install packages, clone repositories, execute
shell commands, register dynamic routes, register new policy actions, activate
capabilities, call external services, or mutate source systems. Install plans
are records only and always keep `executable=false` and
`execution_allowed=false` in v0.1.

## Contracts

- `ExtensionManifest`
- `ExtensionPackage`
- `ExtensionCapabilityDeclaration`
- `ExtensionDependencyDeclaration`
- `ExtensionCompatibilityRequest`
- `ExtensionCompatibilityRun`
- `ExtensionIntakeRequest`
- `ExtensionIntakeRun`
- `ExtensionReviewRequest`
- `ExtensionReview`
- `ExtensionInstallPlan`
- `ExtensionQuery`
- `ExtensionQueryResult`

Manifests are generic and domain-neutral. They reject executable payload keys,
raw secret access, external execution requests, unrestricted autonomy requests,
and domain-specific terms. Declared capabilities and dependencies are metadata
only; they do not activate modules or install dependencies.

## Intake Flow

`manifest -> validation -> package metadata -> declarations -> compatibility -> review -> future install plan`

Dry-run intake validates and records the intake run without creating a package.
Controlled intake may persist package metadata and declarations after policy
approval. Compatibility checks compare local metadata against AION-owned
contracts, settings, policy catalog, runtime configuration, sandbox posture,
and registry boundaries.

## API

- `POST /brain/extensions/manifests/validate`
- `POST /brain/extensions/intake`
- `GET /brain/extensions/intake-runs/{extension_intake_id}`
- `GET /brain/extensions/packages/{extension_package_id}`
- `POST /brain/extensions/query`
- `POST /brain/extensions/packages/{extension_package_id}/archive`
- `DELETE /brain/extensions/packages/{extension_package_id}`
- `GET /brain/extensions/packages/{extension_package_id}/capabilities`
- `GET /brain/extensions/packages/{extension_package_id}/dependencies`
- `POST /brain/extensions/compatibility/check`
- `GET /brain/extensions/compatibility/{extension_compatibility_id}`
- `POST /brain/extensions/packages/{extension_package_id}/review`
- `GET /brain/extensions/reviews`
- `POST /brain/extensions/packages/{extension_package_id}/install-plan`
- `GET /brain/extensions/install-plans/{install_plan_id}`
- `GET /brain/extensions/install-plans`

## SDK and CLI

The Python SDK exposes the registry as `client.extensions`. The CLI exposes
the same metadata-only surface through `aionctl extensions`.

```bash
./scripts/aionctl.sh extensions validate --manifest-file ./manifest.json
./scripts/aionctl.sh extensions intake --manifest-file ./manifest.json
./scripts/aionctl.sh extensions query
./scripts/aionctl.sh extensions compatibility-check extension-package-1
./scripts/aionctl.sh extensions install-plan extension-package-1
```

## Governance

Extension actions are policy-gated with generic `extension.*` action types.
The registry contributes local records to operator queues, release packaging,
freeze gates, security hardening checks, resource registry indexing, audit,
provenance, and visual telemetry. These integrations are advisory and
records-first.

Extension Registry data must not expose hidden reasoning, chain-of-thought,
raw prompts, raw headers, provider payloads, raw secrets, SQLAlchemy rows,
third-party client internals, or domain-specific workflow logic.
