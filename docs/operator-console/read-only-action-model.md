# Operator Console Read-Only Action Model

Operator Console actions in AION-088 are descriptors only. They describe what a
future governed surface might offer; they do not execute.

## Allowed Descriptor Types

- read
- dry-run
- acknowledge
- dismiss with reason
- review record

These descriptors still require policy. They are not direct write paths.

## Forbidden Descriptors

The console must show forbidden descriptors for sensitive views:

- activate module
- activate capability
- load code
- install package
- register route
- enable external model calls
- store credentials
- execute tool
- execute handoff
- bypass policy
- hard delete
- reveal source prompts
- reveal private reasoning
- reveal secrets

## Boundary

Read-only means no activation, no execution, no runtime UI, no package
installation, no code loading, and no privileged operator bypass.
