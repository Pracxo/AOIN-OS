# Model Gateway Reference Provider

AION-233 implements exactly one provider: `deterministic-reference-provider`.
It is a local deterministic simulation component, not an external model
provider. It has no provider SDK, endpoint, network egress, credential read,
authorization header, streaming connection, live model session, connector,
tool, or production effect.

The provider exposes only the simulation adapter surface required by the
controlled gateway. The retained provider response includes fingerprints, byte
counts, deterministic token estimates, synthetic status, output mode, and
effect counters. It does not retain raw prompts, raw context, raw response
bodies, hidden reasoning, or raw provider payloads.

The only model identifiers are `reference-text-sim-v1` and
`reference-json-sim-v1`. `reference-text-sim-v1` supports text simulation.
`reference-json-sim-v1` supports text simulation and restricted structured JSON
simulation. All outputs remain untrusted and cannot become facts, approvals,
memory, beliefs, policy, connector requests, tool requests, actions, deployment
decisions, or successor authorizations.
