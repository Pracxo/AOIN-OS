# Secure Runtime State Machine

The AION-231 state machine is closed. Every transition is explicit and
receipt-bound.

## States

- `drafted`
- `authorized`
- `identity_assertion_verified`
- `request_identity_bound`
- `actor_context_bound`
- `replay_validation_passed`
- `runtime_guard_ready`
- `session_active`
- `request_validated`
- `capability_plan_created`
- `policy_evaluated`
- `risk_evaluated`
- `guardrails_evaluated`
- `approval_validated`
- `simulated_dispatch_completed`
- `response_recorded`
- `session_closed`

## Terminal States

- `abstained`
- `blocked`
- `killed`
- `expired`
- `failed`

## Transition Rules

- Every transition is explicit.
- Every transition is receipt-bound.
- No skipped stage is allowed.
- No automatic continuation is allowed.
- No transition after session expiry is allowed.
- No transition after kill-switch activation is allowed.
- Identity verification precedes ActorContext.
- Replay validation precedes session activation.
- Policy, risk, and guardrails precede dispatch.
- Approval validation precedes any approval-gated dispatch.
- Dispatch remains deterministic and side-effect-free.
- Session close leaves zero active requests.
