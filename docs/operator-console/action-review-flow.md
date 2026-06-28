# Action Review Flow

Operator action review records capture a reviewer decision about a dry-run
request.

Review decisions:

- `acknowledge`
- `dismiss`
- `request_changes`
- `approve_preview_only`
- `reject`
- `block`

Review semantics:

- A review record may reference open blockers.
- `approval_present=true` is stored as review context only.
- `execution_allowed` remains `false`.
- Dismissal does not change the request into an executable command.
- Future write support must pass a separate architecture and policy gate.

The review API is scoped and policy-gated by `operator_action.review`.

## AION-097 Review Authorization

Review creation must pass dry-run action authorization for a reviewer role.
Review records remain record-only evidence; approval context does not execute,
activate, write, or call external systems.
