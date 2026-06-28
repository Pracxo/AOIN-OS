# Dev Identity Simulation

Dev identity simulation creates synthetic local operator contexts for console development.

Simulation accepts an actor id, workspace id, local roles, owner scope, and safe metadata. It returns a `LocalAuthContext` that can be used to preview role-aware console filtering.

Simulation rules:

- identities are synthetic and local only
- production identity is always false
- credential presence is always false
- session presence is always false
- write, execute, activation, and external calls are always false
- policy and audit boundaries still apply

This is not login. It does not prove user identity and must not be represented as production auth.

## AION-095 Session Preview Compatibility

Dev identity simulation may feed a local session preview for Operator Console
filtering. The preview stays synthetic and read-only; it does not authenticate
users, issue browser state, persist sessions, or grant privileged actions.

## AION-096 Role Matrix Compatibility

Simulated identities may feed the role permission proof matrix. The matrix
uses only local role labels and owner scope metadata; it does not authenticate
users or create runtime sessions.
