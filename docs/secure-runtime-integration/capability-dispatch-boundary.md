# Secure Runtime Capability Dispatch Boundary

AION-231 may create capability invocation plans. It may not execute
capabilities.

## Authorized Dispatch Shape

- Closed allowlist.
- Deterministic plan IDs.
- Policy binding.
- Risk binding.
- Guardrail binding.
- Approval evidence bundle binding.
- Side-effect budget binding.
- Runtime guard decision binding.
- Redacted stage receipts.
- Audit and trace correlation.

## Disabled Dispatch Effects

Actual tool execution, shell commands, subprocesses, browser automation,
connector execution, model-provider calls, module code loading, dynamic route
registration, production writes, production memory, production policy, source
mutation, Git mutation, deployment, and model-weight changes remain disabled.
