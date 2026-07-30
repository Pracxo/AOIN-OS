# Secure Runtime Operator Model

AION-231 is an operator-invoked local runtime foundation. It is not a public
service, login flow, deployed runtime, or autonomous background process.

## Operator Responsibilities

- Explicitly start a local session.
- Supply offline identity assertion evidence.
- Review request identity and ActorContext binding.
- Review capability plan, policy, risk, guardrail, approval, and budget
  evidence.
- Keep the kill switch available.
- Close the session explicitly.

## Operator Review Items

Operator review items are redacted records containing decision IDs,
fingerprints, counters, terminal state, and findings. They do not contain raw
credentials, tokens, private keys, protected material, hidden reasoning, or
production data.
