# Console View Access Filtering

Role filtering applies to read-only console view models. It can hide or mark unavailable sections that a role should not inspect, remove disallowed descriptor-only actions, and preserve blockers and forbidden descriptors.

Filtering accepts a `LocalAuthContext`, a `LocalSessionContext`, or roles metadata. If no role context is supplied, the existing view-model behavior is preserved.

Unknown roles and unknown views fail closed. The source view model is copied before filtering so source records are not mutated.

Filtering never grants writes, execution, activation, external calls, production auth, or provider enablement.
