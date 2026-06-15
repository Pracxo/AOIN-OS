# Capability Model

Future modules register capabilities with AION Brain. AION sees capability
contracts, not domain internals.

Each capability should declare:

- Stable capability ID and module version.
- Input and output schema.
- Required permissions.
- Risk level.
- Memory read and write scopes.
- Events subscribed and published.
- Execution mode.

The Brain uses these declarations for planning, policy, execution, tracing, and
audit. Modules do not bypass Brain policy.

The Capability Registry stores what can be done. Module Runtime records store
where and how it can be done. Capability Binding connects a capability to a
runtime and invocation mode. Capability Runtime Gateway controls invocation.

Capability invocation remains policy-gated. A registered capability is a
contract declaration, not proof that executable runtime is available. Runtime
registration does not imply execution approval.

In v0.1, `CapabilityInvoker` delegates to `CapabilityRuntimeGateway` when a
runtime gateway is configured. The gateway supports dry-run validation without
calling an adapter and controlled execution only through the safe
`local_internal` runtime. That runtime supports only generic internal
capabilities: `aion.internal.noop`, `aion.internal.echo`,
`aion.internal.validate_payload`, and `aion.internal.describe_invocation`.

Modules never self-authorize. MCP is an optional compatibility protocol, not
AION's internal governance contract. HTTP remains a placeholder in v0.1. MCP
can discover and map tools into AION capabilities, but controlled external
execution is disabled by default.

## MCP Capability Mapping

MCP tools can be mapped into AION capabilities through
`MCPCapabilityMapping`. The mapping creates AION-owned capability metadata:
risk level, permissions, memory read scopes, memory write scopes, execution
mode, timeout, audit level, input schema, and output schema. MCP supplies tool
interoperability metadata only; it does not supply authorization semantics.

The deterministic mapper uses generic IDs:

- `module_id`: `mcp.{server_name}`
- `capability_id`: `mcp.{server_name}.{sanitized_tool_name}`

It does not infer domain risk, permissions, or memory scope from tool names.
All mapped capabilities include generic invocation permissions and remain
subject to AION policy.

Registered MCP capabilities do not imply controlled execution permission.
Dry-run is the default safe path and returns structured validation results
without calling MCP. Controlled invocation requires MCP to be explicitly
enabled, the runtime to pass transport safety checks, policy to allow the
action, and approval when risk requires it.

## Actor and Workspace Context

Future modules register and invoke capabilities under AION-owned actor and
workspace context. Module actors use generic `module` actor records and
workspace memberships when they need scoped access. Capability manifests may
declare required permissions and memory scopes, but the Brain resolves
permission grants and scopes before capability registration, listing, binding,
or invocation.

Modules cannot mint their own permissions, bypass workspace membership, or
self-authorize through MCP, HTTP, or runtime configuration. The capability
boundary remains a contract declaration; identity, scope, policy, and audit are
owned by AION Brain.

## Capability Certification

Future modules must pass certification before trusted registration.
Certification validates schemas, risk, permissions, memory scopes, policy,
autonomy, dry-run behavior, and audit metadata.

Certification does not execute module code in v0.1. The AION Capability
Manifest remains the internal governance contract used by the Brain.

## Sandbox Boundary

Future controlled capability invocation must pass sandbox validation before a
runtime can act. Capabilities and modules declare runtime permissions, secret
refs, connector refs, and sandbox profile metadata as references only.

Runtime permissions declare what a capability or module may access. Secret refs
and connector refs must be explicit. Manifests must not contain raw secrets,
tokens, passwords, authorization headers, raw endpoint credentials, or wildcard
egress. Wildcard egress is denied in v0.1.

The sandbox boundary does not execute module code in v0.1. It validates
metadata, policy, risk, approval, autonomy, and dry-run constraints before any
future controlled execution layer can be trusted.
