# Secure Runtime Session Lifecycle

AION-231 may implement a single explicit local operator session lifecycle. A
session is not a browser session, public login, token, cookie, or production
authentication flow.

## Lifecycle

1. `drafted`
2. `authorized`
3. `identity_assertion_verified`
4. `request_identity_bound`
5. `actor_context_bound`
6. `replay_validation_passed`
7. `runtime_guard_ready`
8. `session_active`
9. `request_validated`
10. `capability_plan_created`
11. `policy_evaluated`
12. `risk_evaluated`
13. `guardrails_evaluated`
14. `approval_validated`
15. `simulated_dispatch_completed`
16. `response_recorded`
17. `session_closed`

Terminal states are `abstained`, `blocked`, `killed`, `expired`, and `failed`.

## Limits

Only one local operator session may exist. A session lasts at most 3600 seconds,
accepts at most 100 requests, allows at most four concurrent requests, and
leaves zero active requests at close.
