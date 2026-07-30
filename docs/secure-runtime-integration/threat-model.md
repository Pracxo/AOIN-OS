# Secure Runtime Integration Threat Model

AION-231 must block unsafe local runtime progression before any later
model-gateway, connector, module, production, deployment, or release work can
be considered.

## Threats

- Caller-controlled identity headers impersonate an operator.
- Missing replay validation permits duplicate request acceptance.
- ActorContext is constructed before identity verification.
- Capability plans bypass policy, risk, guardrail, or approval evidence.
- Side-effect counters drift from the authorized zero limits.
- Kill-switch activation is ignored.
- Runtime evidence leaks credentials, tokens, private keys, or protected
  material.
- Deterministic dispatch simulation is mistaken for actual execution.
- Future model, connector, tool, module, or deployment work starts without a
  separate authorization.

## Controls

- Fail closed for missing or invalid identity, replay, policy, risk,
  guardrail, approval, budget, guard, kill-switch, or audit evidence.
- Keep all public network, model-provider, connector, tool, shell, subprocess,
  browser, module, production, source, Git, deployment, and model-training
  effects at zero.
- Keep AION-232 as the mandatory formal evaluation before any later
  authorization decision.
