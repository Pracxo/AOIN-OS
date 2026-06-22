# ADR 0023: Risk, Guardrail, and Approval Control Plane

## Decision

AION Brain adds a deterministic Risk Engine, generic Guardrail Engine, and
Approval Control Plane before side-effect-capable work.

Risk scoring produces `RiskAssessment` records. Guardrails produce
`GuardrailDecision` records. Approval creates pending `ApprovalRequest` records
and terminal `ApprovalDecision` records.

## Reason

AION needs a common governance boundary before model calls, capability
invocation, controlled execution, workflow runs, task runs, MCP calls, and skill
activation. The boundary must be generic so future vertical modules cannot
self-authorize or smuggle domain-specific rules into Brain core.

## Consequences

High-risk generic actions can pause as pending approvals. Critical guardrail
matches can block before any adapter is called. Approval evidence can be
supplied to a later governed request, but approval never automatically resumes
or executes the original action in v0.1.

The control plane emits visual telemetry for risk assessments, guardrail
decisions, and approval lifecycle changes.

## Constraints

- No domain-specific guardrails or policy actions.
- No external notification service.
- No automatic post-approval execution.
- No vendor-specific objects in public Brain contracts.
- No secrets in risk, guardrail, approval, telemetry, or observability payloads.
