# Operator Action Boundaries

AION Operator Console must preserve policy, audit, approval, and dry-run gates.
AION-087 creates this boundary document only; it adds no runtime UI.

## Allowed future UI actions

- run dry-run checks
- seed local defaults
- run setup doctor
- run golden path
- run RC gate
- run release smoke
- validate extension manifest
- run binding validation
- run conformance dry-run
- run module mock invocation
- run provider egress preview
- acknowledge notifications
- dismiss non-blocking findings with reason
- create operator review records

## Forbidden future UI actions

- activate module
- activate capability
- load code
- install package
- register route
- enable external model calls
- store credentials
- execute model-generated tools
- approve hidden action without audit
- bypass policy
- hard delete records
- mutate production config

## Boundary rule

Future console actions must call existing governed APIs or CLI-backed dry-run
paths. The console must not become a privileged backdoor around policy,
approval, audit, module activation, provider hardening, or runtime config
governance.
