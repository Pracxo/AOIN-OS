# Secure Runtime Guard

The runtime guard is the fail-closed decision point for each AION-231 request.
It composes identity status, request identity, ActorContext, replay validation,
capability allowlist membership, policy, risk, guardrails, approval evidence,
side-effect budget, kill-switch state, session expiry, and audit readiness.

## Guard Result

The guard may return only:

- `allow_simulated_dispatch`
- `abstain`
- `block`
- `kill`
- `expire`
- `fail`

`allow_simulated_dispatch` permits only deterministic local dispatch
simulation. It does not execute a tool, call a provider, call a connector,
write production state, mutate source, mutate Git, deploy, or create release
artifacts.
