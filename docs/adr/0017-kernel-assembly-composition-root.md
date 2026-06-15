# ADR 0017: Kernel Assembly Composition Root

## Decision

AION Brain uses `KernelContainer` as its single composition root and an
AppFactory for FastAPI creation. The kernel exposes local self-test,
contract-export, boot-diagnostic, service-registry, and architecture-boundary
APIs. OpenAPI and core Pydantic schemas are exported as AION-owned contracts.

## Reason

AION needs one inspectable assembly boundary before stronger adapters and
external modules are introduced. Process-wide construction prevents routes
from creating inconsistent service graphs and makes adapter selection explicit.

## Consequences

Future Codex tasks wire services through the container and register them in the
kernel service registry. Routes consume the process-wide container from app
state. Boot and self-test results provide local evidence of assembly health.

## Constraints

- No direct vendor imports outside approved adapter files.
- No domain-specific subsystems in Brain core.
- No external AI calls or module execution in the kernel self-test.
- Public contracts remain provider-neutral.
