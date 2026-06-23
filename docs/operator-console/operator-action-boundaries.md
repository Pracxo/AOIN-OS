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

## AION-088 descriptor boundary

AION-088 exposes action descriptors only. The API and CLI can describe safe
dry-run or review paths and can describe forbidden actions, but they do not
execute them.

The read-only action model keeps no runtime UI, no raw prompt exposure, no
hidden reasoning exposure, no secret exposure, no activation, and no execution.

## AION-092 governed action boundary

AION-092 adds governed operator action request records. They are still bounded:
requests are dry-run only, previews are descriptive only, reviews are records
only, and blocker dismissal does not unlock execution.

The action boundary matrix is defined in
`docs/operator-console/action-boundary-matrix.md`.

## AION-093 auth boundary

AION-093 does not authorize new runtime actions. The local auth design may
describe which roles can read, request dry-runs, preview, review, dismiss
findings, and export redacted summaries, but policy remains authoritative.

No role may execute, activate, load code, register routes, enable providers,
store credentials, hard delete, or bypass policy in this phase.

## AION-094 local auth action filtering

Role filtering may remove allowed action descriptors from a read-only view
model when a local role cannot request them. It never adds write actions and
keeps forbidden descriptors visible as safety evidence.
