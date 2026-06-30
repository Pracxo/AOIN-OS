# Operator Connector Boundary Matrix

## Purpose

This matrix maps the post-v0.1 operator and connector platform boundaries into
one review table for AION-117.

| Area | Operator state | Connector state | Runtime state | Allowed today | Future-only | Gate script | Release blocker if failed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Static console | Read-only local static UI | Displays connector evidence only | No runtime UI server | Bundled JSON preview | Runtime console actions | `./scripts/static-console-safety-check.sh` | Yes | No package files or frontend build step |
| Operator actions | Descriptors and dry-run reviews | Connector actions denied | No write execution | Preview blockers and reviews | Governed write execution | `./scripts/operator-actions-check.sh` | Yes | Write execution needs future ADR |
| Action authorization | Role-aware dry-run deny matrix | Connector actions denied | No action dispatch | Denial evidence | Real action dispatch | `./scripts/action-authorization-check.sh` | Yes | No privileged bypass |
| Local auth | Dev-only mock identity and read-only session previews | No connector identity runtime | Production auth disabled | Synthetic actor context | Production auth runtime | `./scripts/auth-prototype-review.sh` | Yes | OAuth, OIDC, and SAML stay future-only |
| Module lifecycle | Read-only lifecycle dashboard | Connector activation denied | Activation disabled | Metadata review | Module activation and registration | `./scripts/module-activation-design-review.sh` | Yes | No code loading |
| Connector runtime | Operator sees disabled status only | Runtime disabled | No connector execution | Status and boundary evidence | Connector runtime implementation | `./scripts/connector-runtime-review.sh` | Yes | No route registration |
| Connector simulator | Operator sees synthetic dry-run evidence | Local fixtures only | No external call | Deterministic replay | Live connector calls | `./scripts/connector-simulator-check.sh` | Yes | No trusted ingress |
| Connector policy | Operator sees denial catalog | Policy catalog is read-only | No allow path | Dry-run policy checks | Runtime allow path | `./scripts/connector-policy-check.sh` | Yes | Denials remain visible |
| Connector credentials | Operator sees readiness/redaction evidence | No credential values | Storage disabled | Architecture evidence | Credential storage | `./scripts/connector-credential-check.sh` | Yes | No token storage |
| Connector sandbox | Operator sees isolation design evidence | No sandbox process | Execution disabled | Design readiness | Sandbox execution | `./scripts/connector-sandbox-check.sh` | Yes | No filesystem, network, process, import, or package execution |
| Release gate | Operator evidence stays local | Connector release gate remains strict | No runtime release | Checkpoint scripts | Production release runtime | `./scripts/platform-integration-checkpoint.sh` | Yes | AION-117 composes all prior gates |

## Matrix decision

Every row remains a release blocker. Failure means the post-v0.1 platform
checkpoint is not complete and future runtime work must stay blocked.
