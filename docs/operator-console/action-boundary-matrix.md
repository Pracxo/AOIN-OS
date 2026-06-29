# Action Boundary Matrix

| Boundary | AION-092 State | Reason |
| --- | --- | --- |
| Request creation | Allowed | Creates local metadata only |
| Preview creation | Allowed | Computes expected and blocked effects only |
| Blocker creation | Allowed | Records governance constraints |
| Review creation | Allowed | Captures operator decision only |
| Blocker dismissal | Allowed | Records reviewer context only |
| Execution | Disabled | No runtime action path exists |
| External calls | Disabled | No provider or external service call path exists |
| Activation | Disabled | Module and capability activation remain out of scope |
| Runtime config mutation | Disabled | Runtime config remains source-of-truth protected |
| Hard delete | Disabled | Records remain soft-governed |

Every public contract keeps execution, external calls, and activation flags
false. The dry-run flow is a governance surface, not a command surface.

## AION-097 Authorization Matrix

Action authorization adds role, policy, and session gates to the matrix. An
allowed decision can only create dry-run preview or review evidence. Denied
decisions remain visible and do not create an execution path.

## AION-107 Write-Path Matrix

| Boundary | AION-107 State | Reason |
| --- | --- | --- |
| Write-path architecture | Allowed | Design and evidence only |
| Approval boundary | Allowed | Approval does not execute |
| Execution boundary | Future-only | No execution path exists |
| Rollback model | Allowed | Design prerequisite only |
| Separation of duties | Allowed | Role model prerequisite only |
| Future execution readiness | Disabled | future_execution_ready is not reachable today |
| Future execution | Disabled | future_executed is not reachable today |
| External calls | Disabled | Connector runtime remains absent |
| Activation | Disabled | Module and capability activation remain out of scope |
