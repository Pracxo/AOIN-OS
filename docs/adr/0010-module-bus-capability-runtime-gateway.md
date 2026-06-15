# ADR 0010: Module Bus and Capability Runtime Gateway

## Status

Accepted.

## Decision

AION Brain adds a Module Bus and `CapabilityRuntimeGateway` as the only runtime
invocation path for capabilities.

HTTP and MCP runtimes remain placeholders in v0.1. The only executable runtime
in v0.1 is the safe `local_internal` runtime, which supports generic internal
capabilities only.

## Reason

Future modules need a stable plug-in boundary that does not leak module
internals, HTTP client objects, MCP SDK objects, shell commands, browser
drivers, SaaS APIs, or vendor SDKs into Brain public contracts.

The gateway lets AION own runtime registration, capability binding, runtime
health records, invocation policy gates, audit records, telemetry semantics,
and execution safety.

## Consequence

AION can accept future modules without changing Brain contracts. New runtimes
can be implemented behind adapters while API callers continue to use
`ModuleRuntime`, `CapabilityRuntimeBinding`, `ModuleHealthCheck`,
`CapabilityInvocationRequest`, and `CapabilityInvocationResult`.

## Constraints

No external module execution exists in v0.1. No domain-specific runtime logic
exists in Brain core. HTTP and MCP adapters do not perform network calls and do
not import MCP SDKs.
