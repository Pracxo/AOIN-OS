# Operator Console API Contract Audit

The AION-088 contract audit checks that the console contract is safe to consume
before a UI exists.

## Checks

- required Operator Console docs exist
- JSON examples parse
- examples contain no secret-shaped or private-source payloads
- forbidden actions include reasons
- data source map includes required module and provider views
- frontend package/config files are absent
- view models remain read-only

The audit runs locally. It does not call external services, install packages,
execute tools, activate modules, or create persistent console state.

## API

`POST /brain/operator-console/audit`

The endpoint returns `ConsoleAuditResult` when local checks pass. If a frontend
file appears in the scanned tree, the audit fails closed.

Required documentation posture:

- read-only
- no runtime UI
- no raw prompt exposure
- no hidden reasoning exposure
- no secret exposure
- no activation
- no execution
