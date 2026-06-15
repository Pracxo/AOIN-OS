# ADR 0013: Identity, Workspace, and Scope Control Plane

## Status

Accepted

## Context

AION Brain needs request-time actor, workspace, scope, and permission context
before production authentication exists. Future modules must be governed by the
Brain's policy and audit boundaries, but v0.1 must remain local, deterministic,
domain-neutral, and free of external identity-provider coupling.

## Decision

AION Brain will own local development identity metadata through:

- `ActorRecord`
- `WorkspaceRecord`
- `WorkspaceMembership`
- `PermissionGrant`
- `ActorContext`
- `ScopeResolutionRequest`
- `ScopeResolution`

The API accepts development context only through `X-AION-*` headers. In
development mode, AION can synthesize a default local owner context for setup
and smoke testing. Production authentication is deferred.

All actor, workspace, membership, permission, and scope operations pass through
the generic policy boundary. Scope resolution applies deny-wins permission
semantics, blocks disabled actors, constrains archived workspaces, and emits
visual telemetry.

## Constraints

- No OAuth, SSO, bearer token parsing, cookies, sessions, or external identity
  providers are introduced in v0.1.
- No domain-specific permissions or vertical workflow roles are introduced.
- Modules never self-authorize.
- Public APIs return AION-owned contracts or plain JSON derived from them.
- Metadata rejects secret-like keys.

## Consequences

AION can build and test real-time Brain flows locally with stable actor,
workspace, scope, and permission context from the start. The control plane is
replaceable later: production auth can map into AION-owned actor and scope
contracts without changing Brain public APIs or module governance rules.
