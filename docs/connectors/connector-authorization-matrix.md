# Connector Authorization Matrix

The connector authorization matrix maps roles to connector policy actions.
It is deterministic local data used by the dry-run gate and static console
preview.

Matrix guarantees:

- all `runtime_allowed` values are false
- all `external_call_allowed` values are false
- all `credential_access_allowed` values are false
- all `token_access_allowed` values are false
- all `activation_allowed` values are false
- future runtime actions are explicit denials

Viewer and auditor roles may read catalog evidence. Operator, reviewer, and
admin roles may dry-run safe preview actions. No role can approve connector
runtime, external egress, credential handling, token handling, activation,
route registration, tool execution, or write execution.
