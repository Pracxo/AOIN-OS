# Connector Capability Declaration

## Purpose

Connector capability declarations are future metadata records. They are not
runtime permissions, active capabilities, or execution commands.

## Connector Manifest Fields

Future connector manifests may declare:

- connector key
- display name
- description
- declared capabilities
- required scopes
- required policies
- required sandbox profile
- credential needs
- egress contract
- ingress contract
- dry-run support
- rate limits
- audit tags
- provenance tags
- rollback plan

## Capability Declarations

Capability declarations must be generic and domain-neutral. They describe what
a connector might support after validation; they do not activate capability
invocation.

## Required Scopes

Required scopes must be explicit and minimal. Overbroad scopes are no-go
conditions until reviewed by policy, action authorization, and operator gates.

## Required Policies

Future connector actions must map to generic policy actions. Connector metadata
must not create policy actions dynamically.

## Required Sandbox

Future connectors must declare sandbox posture before runtime work. Sandbox
requirements must include network posture, credential isolation, egress
constraints, ingress normalization, and audit capture.

## Dry-Run Support

Future connectors should support dry-run previews for egress, ingress,
credential reference checks, rate-limit checks, policy decisions, and operator
review. Dry-run support is not runtime execution.

## Rate Limits

Connector declarations must include rate-limit expectations. Runtime calls
remain disabled until rate-limit enforcement and failure behavior are reviewed.

## Audit Tags

Connector declarations must include audit tags for connector reference, action,
scope, credential reference, egress preview, ingress normalization, and operator
review.

## Egress/Ingress Contracts

Egress and ingress contracts must define allowed fields, blocked fields,
redaction state, provenance state, policy decision refs, and operator review
requirements.

## No Executable Payloads

Connector manifests must not contain executable payloads, code blobs,
entrypoints, package install commands, dynamic imports, or source downloads.

## No Dynamic Routes

Connector manifests must not declare dynamic API routes, SDK methods, CLI
commands, webhook handlers, callback routes, or runtime registration paths.
