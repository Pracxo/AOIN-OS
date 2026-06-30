# Connector Policy Action Catalog

AION-111 adds a connector policy action catalog for read-only and dry-run
authorization preview. The catalog lists connector runtime preview actions,
synthetic simulator actions, and connector policy actions without creating a
connector runtime.

Catalog actions:

- `connector_policy.catalog.read`
- `connector_policy.matrix.read`
- `connector_policy.dry_run`
- `connector_policy.traceability.read`

Existing disabled connector runtime and simulator actions remain listed for
traceability. Every catalog entry sets `allowed_in_runtime=false`,
`requires_connector_runtime=false`, `requires_credentials=false`, and
`requires_external_call=false`.

Explicit denied future actions:

- `connector.runtime.enable`
- `connector.external.call`
- `connector.credentials.store`
- `connector.tokens.store`
- `connector.activate`
- `connector.route.register`
- `connector.tool.execute`
- `connector.write.execute`
- `connector.provider.call`

The catalog is not a runtime grant. It cannot enable external calls,
credential access, token access, activation, route registration, tool
execution, or write execution.

## AION-113 Credential Preview Actions

AION-113 adds connector credential read/preview actions to the platform policy
catalog. These actions expose boundary, lifecycle, authorization, readiness,
redaction-preview, and status evidence only. They do not grant credential
storage, token storage, secret material access, external identity runtime, or
connector runtime credential access.
## AION-114 Release Gate Input

The connector policy catalog is required release evidence. Runtime allow paths,
external calls, credential/token access, sandbox execution, activation, and
route registration remain denied until a future ADR changes the boundary.
