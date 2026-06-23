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
