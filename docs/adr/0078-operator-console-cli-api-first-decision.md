# 0078: Operator Console CLI/API-First Decision

## Status

Accepted

## Context

AION Brain v0.1.0 is frozen and tagged. Post-v0.1 work has added module
lifecycle governance, module mock runtime evidence, and model provider
hardening without enabling activation, execution, external calls, or runtime
registration.

AION now needs operator experience semantics before any frontend runtime.

## Decision

Remain CLI/API-first after v0.1.

AION-087 creates operator console strategy only. No frontend runtime or
dependencies are added.

Future UI must consume existing Brain APIs and preserve policy, audit, and
approval gates. Future UI must not expose raw prompts, hidden reasoning, or
secrets. Future UI must not activate modules, activate capabilities, load code,
install packages, register routes, bypass policy, or enable external calls.

## Reason

Module lifecycle and provider hardening flows need stable operator semantics
before UI implementation. A strategy and workflow map lets AION define views,
data safety, no-go conditions, and dry-run controls without adding a new
control surface.

## Consequences

UI work can begin later with clear view specs and no-go conditions. The next
appropriate UI milestone is API contract audit and view-model extraction, not
runtime UI implementation.

## Constraints

- no UI runtime
- no frontend dependencies
- no privileged bypass
- no module activation
- no capability activation
- no code loading
- no package installation
- no external model calls
