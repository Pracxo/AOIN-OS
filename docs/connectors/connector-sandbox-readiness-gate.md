# Connector Sandbox Readiness Gate

The connector sandbox readiness gate evaluates a declared connector key,
owner scope, capability list, policy actions, and evidence references. It
returns readiness evidence without executing connector code.

The gate can return `ready` only for preview-safe capability declarations.
Requests for denied future sandbox capabilities return `blocked` and include
the relevant blocker keys. Unknown capability requests also return `blocked`.

Every readiness result keeps these values false:

- `runtime_execution_allowed`
- `filesystem_access_allowed`
- `network_access_allowed`
- `credential_access_allowed`
- `token_access_allowed`
- `process_spawn_allowed`
- `dynamic_import_allowed`
- `package_install_allowed`
- `connector_activation_allowed`

The gate requires audit and provenance evidence. It is not a runtime approval
and cannot bypass connector policy, release gates, or operator review.
