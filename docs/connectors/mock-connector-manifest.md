# Mock Connector Manifest

## Purpose

The AION-108 mock connector manifest is synthetic metadata for local preview
validation. It is not a connector registration record and cannot activate a
connector.

## Required Shape

The manifest declares a dotted lowercase `connector_key`, name, description,
version, owner scope, connector type, supported modes, declared capabilities,
required policy actions, required scopes, sandbox requirement, dry-run support,
and explicit disabled runtime requirements.

## Rejected Fields

AION-108 rejects manifests when:

- `external_calls_required=true`
- `credentials_required=true`
- `routes_declared` is non-empty
- `dry_run_supported=false`
- metadata contains secrets, raw prompts, or hidden reasoning

Valid manifests normalize to preview-only evidence with external calls,
credentials, and routes set to false or empty.
