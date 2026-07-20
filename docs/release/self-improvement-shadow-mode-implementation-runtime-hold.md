# Shadow-Mode Implementation Runtime Hold

Runtime hold remains active after AION-178:

- `shadow_mode_implemented=true`
- `shadow_mode_implementation_state=implemented_operator_invoked_disabled`
- `shadow_mode_runtime_enabled=false`
- `operator_invoked_shadow_runs_supported=true`
- background loops, production event streams, network calls, connector calls,
  provider calls, source mutation, Git mutation, real PR creation, approval
  creation, merge, canary, deployment, promotion, and model training remain
  disabled.
