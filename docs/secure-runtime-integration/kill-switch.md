# Secure Runtime Kill Switch

AION-231 must check an operator kill switch before request progression and
again before simulated dispatch.

## Requirements

- Kill state is local and explicit.
- Kill state is included in every guard decision.
- Kill activation blocks all further transitions.
- Kill activation records a terminal stage receipt.
- Kill activation closes the session with zero active requests.

The kill switch does not create production policy, mutate production policy,
invoke a provider, call a connector, execute a tool, mutate source, mutate Git,
or deploy.
