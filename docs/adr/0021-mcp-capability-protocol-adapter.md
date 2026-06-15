# ADR 0021: MCP Capability Protocol Adapter

## Status

Accepted.

## Context

AION Brain needs future interoperability with external tools without allowing
external protocols to define Brain governance. The Capability Registry, Module
Bus, Policy Engine, Kernel Container, and Visual Telemetry are already owned by
AION contracts. MCP can provide a useful tool protocol later, but it must remain
behind AION boundaries.

## Decision

Implement MCP behind `CapabilityProtocolAdapter` and `MCPRuntimeAdapter`.

Keep MCP disabled by default.

Keep AION Capability Manifest as the internal governance contract.

Do not execute real external MCP tools by default.

Do not allow shell or network execution in the normal v0.1 path.

Allow deterministic `in_memory_fake` MCP tools for tests and local demos only.

Restrict direct MCP SDK import logic to `aion_brain/mcp/compat.py`.

## Reason

Future modules need standard tool interoperability without surrendering Brain
governance. AION must continue to own capability IDs, risk, permissions, memory
scope, execution mode, audit level, policy gates, invocation records, telemetry,
and public API contracts.

## Consequences

AION can map external MCP tools into policy-gated AION capabilities later.

Regular tests pass without the MCP SDK installed.

Public AION APIs return AION contracts only and never expose MCP SDK clients,
sessions, transports, prompts, resources, or raw SDK objects.

Real MCP network and stdio use require explicit configuration, policy approval,
and transport permission.

## Constraints

No domain-specific tool logic belongs in the MCP adapter.

No shell execution, subprocess use, or real network call may occur in normal
tests.

MCP tools do not self-authorize and do not define AION policy, permissions,
memory scope, risk, or audit semantics.
